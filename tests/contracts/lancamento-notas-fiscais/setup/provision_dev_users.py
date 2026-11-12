#!/usr/bin/env python3
"""Provisiona usuários de contrato LNF somente no Keycloak/Core DEV local.

Idempotente. Aborta se a base não for localhost/127.0.0.1.
Não imprime senhas. Grava tokens em ../.env.local (gitignored).
"""

from __future__ import annotations

import json
import secrets
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
# DEV: infra/.env | HML: LNF_PROVISION_ENV=infra/.env.hml (no servidor)
INFRA_ENV = Path(
    __import__("os").environ.get("LNF_PROVISION_ENV")
    or (REPO / "infra" / ".env")
)
MANIFEST = REPO / "plugins" / "lancamento-notas-fiscais" / "lancamento-notas-fiscais.manifest.json"
ENV_LOCAL = Path(
    __import__("os").environ.get("LNF_ENV_LOCAL") or (ROOT / ".env.local")
)

PROFILES: dict[str, dict] = {
    "P0": {"username": "lnf-contract-p0", "permissions": [], "superadmin": False},
    "P1": {"username": "lnf-contract-p1", "permissions": ["lancamento-notas-fiscais.access"], "superadmin": False},
    "P2": {"username": "lnf-contract-p2", "permissions": ["lancamento-notas-fiscais.view.filial-01"], "superadmin": False},
    "P3": {"username": "lnf-contract-p3", "permissions": ["lancamento-notas-fiscais.view.filial-02"], "superadmin": False},
    "P4": {"username": "lnf-contract-p4", "permissions": ["lancamento-notas-fiscais.view"], "superadmin": False},
    "P5": {"username": "lnf-contract-p5", "permissions": ["lancamento-notas-fiscais.create"], "superadmin": False},
    "P6": {"username": "lnf-contract-p6", "permissions": ["lancamento-notas-fiscais.process"], "superadmin": False},
    # process + view.filial-01: Core filter_user_ids_with_app_access só libera o
    # sourceApp se o destinatário tiver permissão de alguma app_route (GET /me/apps).
    # Rotas LNF usam view.filial-01/02 e review-unmapped-products — .access sozinho não destrava.
    "P6B": {
        "username": "lnf-contract-p6b",
        "permissions": [
            "lancamento-notas-fiscais.process",
            "lancamento-notas-fiscais.view.filial-01",
        ],
        "superadmin": False,
    },
    "P7": {"username": "lnf-contract-p7", "permissions": ["lancamento-notas-fiscais.manage"], "superadmin": False},
    "P8": {"username": "lnf-contract-p8", "permissions": ["lancamento-notas-fiscais.review-unmapped-products"], "superadmin": False},
    "P9": {"username": "lnf-contract-p9", "permissions": [], "superadmin": True},
    # Perfis combinados (realidade de produção): create + view.filial-XX
    "P11": {
        "username": "lnf-contract-p11",
        "permissions": ["lancamento-notas-fiscais.create", "lancamento-notas-fiscais.view.filial-01"],
        "superadmin": False,
    },
    "P12": {
        "username": "lnf-contract-p12",
        "permissions": ["lancamento-notas-fiscais.create", "lancamento-notas-fiscais.view.filial-02"],
        "superadmin": False,
    },
}

EXPECTED_LNF = {
    "P0": set(),
    "P1": {"lancamento-notas-fiscais.access"},
    "P2": {"lancamento-notas-fiscais.view.filial-01"},
    "P3": {"lancamento-notas-fiscais.view.filial-02"},
    "P4": {"lancamento-notas-fiscais.view"},
    "P5": {"lancamento-notas-fiscais.create"},
    "P6": {"lancamento-notas-fiscais.process"},
    "P6B": {
        "lancamento-notas-fiscais.process",
        "lancamento-notas-fiscais.view.filial-01",
    },
    "P7": {"lancamento-notas-fiscais.manage"},
    "P8": {"lancamento-notas-fiscais.review-unmapped-products"},
    "P11": {"lancamento-notas-fiscais.create", "lancamento-notas-fiscais.view.filial-01"},
    "P12": {"lancamento-notas-fiscais.create", "lancamento-notas-fiscais.view.filial-02"},
}


class Fail(RuntimeError):
    pass


def load_infra() -> dict[str, str]:
    env: dict[str, str] = {}
    for line in INFRA_ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        env[key] = value
    return env


def assert_local(url: str) -> None:
    """Aceita DEV local e HML (192.168.1.237:18443/18080). Recusa PROD."""
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1"}:
        return
    if host == "192.168.1.237":
        port = parsed.port
        if port is None:
            port = 443 if (parsed.scheme or "").lower() == "https" else 80
        if port in {18443, 18080}:
            return
        raise Fail(f"host PROD recusado: {host}:{port} (HML só :18443/:18080)")
    raise Fail(f"host não local/HML: {host}")


def http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: object | None = None,
    form: dict[str, str] | None = None,
    ok: set[int] | None = None,
) -> tuple[int, object]:
    headers: dict[str, str] = {}
    data: bytes | None = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            status = response.status
            payload: object = json.loads(raw) if raw else None
            return status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        payload = None
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw.decode(errors="replace")[:200]
        if ok and exc.code in ok:
            return exc.code, payload
        raise Fail(f"{method} {url} -> {exc.code}: {payload}") from exc


def gen_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(28))


def password_token(base: str, realm: str, client_id: str, username: str, password: str) -> str:
    status, payload = http_json(
        "POST",
        f"{base}/auth/realms/{realm}/protocol/openid-connect/token",
        form={
            "client_id": client_id,
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": "openid profile email",
        },
    )
    if status != 200 or not isinstance(payload, dict) or not payload.get("access_token"):
        raise Fail(f"token falhou para {username}")
    return str(payload["access_token"])


def admin_token(base: str, admin_user: str, admin_pass: str) -> str:
    status, payload = http_json(
        "POST",
        f"{base}/auth/realms/master/protocol/openid-connect/token",
        form={
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_pass,
            "grant_type": "password",
        },
    )
    if status != 200 or not isinstance(payload, dict):
        raise Fail("admin token Keycloak falhou")
    return str(payload["access_token"])


def ensure_kc_user(base: str, realm: str, adm: str, username: str, password: str) -> str:
    email = f"{username}@contract.local"
    status, users = http_json(
        "GET",
        f"{base}/auth/admin/realms/{realm}/users?username={urllib.parse.quote(username)}&exact=true",
        token=adm,
    )
    uid = ""
    if status == 200 and isinstance(users, list) and users:
        uid = str(users[0]["id"])
        http_json(
            "PUT",
            f"{base}/auth/admin/realms/{realm}/users/{uid}",
            token=adm,
            body={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "email": email,
                "firstName": "LNF",
                "lastName": username,
                "requiredActions": [],
            },
            ok={204},
        )
    else:
        http_json(
            "POST",
            f"{base}/auth/admin/realms/{realm}/users",
            token=adm,
            body={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "email": email,
                "firstName": "LNF",
                "lastName": username,
                "requiredActions": [],
            },
            ok={201, 204},
        )
        status, users = http_json(
            "GET",
            f"{base}/auth/admin/realms/{realm}/users?username={urllib.parse.quote(username)}&exact=true",
            token=adm,
        )
        uid = str(users[0]["id"])  # type: ignore[index]
    http_json(
        "PUT",
        f"{base}/auth/admin/realms/{realm}/users/{uid}/reset-password",
        token=adm,
        body={"type": "password", "value": password, "temporary": False},
        ok={204},
    )
    return uid


def ensure_bootstrap_admin(
    base: str,
    realm: str,
    adm: str,
    passwords: dict[str, str],
    *,
    email: str,
) -> str:
    status, users = http_json(
        "GET",
        f"{base}/auth/admin/realms/{realm}/users?email={urllib.parse.quote(email)}&exact=true",
        token=adm,
    )
    if not isinstance(users, list) or not users:
        raise Fail(f"superadmin {email} ausente no Keycloak do alvo")
    uid = str(users[0]["id"])
    password = passwords.get("LNF_BOOTSTRAP_ADMIN_PASSWORD") or gen_password()
    http_json(
        "PUT",
        f"{base}/auth/admin/realms/{realm}/users/{uid}/reset-password",
        token=adm,
        body={"type": "password", "value": password, "temporary": False},
        ok={204},
    )
    passwords["LNF_BOOTSTRAP_ADMIN_USERNAME"] = email
    passwords["LNF_BOOTSTRAP_ADMIN_PASSWORD"] = password
    return password


def register_manifest(core: str, token: str) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    status, payload = http_json(
        "POST",
        f"{core}/admin/apps/register",
        token=token,
        body=manifest,
        ok={200, 201, 400, 409},
    )
    if status in {200, 201}:
        return
    errors = []
    if isinstance(payload, dict):
        errors = payload.get("errors") or []
    codes = {
        str(item.get("code") or "")
        for item in errors
        if isinstance(item, dict)
    }
    if "plugin.version_already_exists" in codes or status == 409:
        return
    raise Fail(f"register manifesto falhou: {status} {payload}")


def list_permissions(core: str, token: str) -> dict[str, str]:
    status, body = http_json("GET", f"{core}/admin/rbac/permissions?page=1&page_size=1000", token=token)
    items: list = []
    if isinstance(body, list):
        items = body
    elif isinstance(body, dict):
        items = body.get("items") or body.get("data") or []
        if isinstance(body.get("data"), dict):
            items = body["data"].get("items") or []
    mapping: dict[str, str] = {}
    for item in items:
        if isinstance(item, dict) and item.get("code") and item.get("id"):
            mapping[str(item["code"])] = str(item["id"])
    return mapping


def ensure_role(core: str, token: str, name: str, permission_ids: list[str]) -> str:
    status, body = http_json(
        "GET",
        f"{core}/admin/rbac/roles?q={urllib.parse.quote(name)}&page=1&page_size=50",
        token=token,
    )
    items = []
    if isinstance(body, dict):
        items = body.get("items") or body.get("data") or []
        if isinstance(body.get("data"), dict):
            items = body["data"].get("items") or []
    role_id = ""
    for item in items:
        if isinstance(item, dict) and item.get("name") == name and item.get("id"):
            role_id = str(item["id"])
            break
    if not role_id:
        status, created = http_json(
            "POST",
            f"{core}/admin/rbac/roles",
            token=token,
            body={"name": name, "description": f"Contrato LNF {name}"},
            ok={201, 200},
        )
        if isinstance(created, dict) and created.get("id"):
            role_id = str(created["id"])
        else:
            raise Fail(f"falha ao criar papel {name}")
    http_json(
        "PUT",
        f"{core}/admin/rbac/roles/{role_id}/permissions",
        token=token,
        body={"permissionIds": permission_ids},
        ok={200},
    )
    return role_id


def ensure_user_roles(core: str, token: str, user_id: str, role_ids: list[str], *, superadmin: bool) -> None:
    http_json(
        "PUT",
        f"{core}/admin/rbac/users/{user_id}/roles",
        token=token,
        body={"roleIds": role_ids},
        ok={200},
    )
    http_json(
        "PUT",
        f"{core}/admin/rbac/users/{user_id}",
        token=token,
        body={"is_superadmin": superadmin},
        ok={200},
    )


def me(core: str, token: str) -> dict:
    status, body = http_json("GET", f"{core}/me", token=token)
    if not isinstance(body, dict):
        raise Fail("/me inválido")
    return body


def lnf_perms(body: dict) -> set[str]:
    perms = body.get("permissions") or body.get("effectivePermissions") or []
    return {p for p in perms if isinstance(p, str) and p.startswith("lancamento-notas-fiscais.")}


def write_env_local(values: dict[str, str]) -> None:
    existing: dict[str, str] = {}
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            existing[key] = value
    existing.update(values)
    lines = [f"{key}={existing[key]}" for key in sorted(existing)]
    ENV_LOCAL.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not INFRA_ENV.is_file():
        raise Fail(f"env ausente: {INFRA_ENV}")
    infra = load_infra()
    base = (
        infra.get("DEV_BASE_URL")
        or infra.get("PUBLIC_BASE_URL")
        or infra.get("DELPI_HML_PUBLIC_ORIGIN")
        or "http://localhost"
    ).rstrip("/")
    assert_local(base)
    core = f"{base}/core-api"
    assert_local(core)
    realm = infra.get("DEV_KC_REALM") or infra.get("KEYCLOAK_REALM") or "delpi"
    client_id = infra.get("DEV_KC_CLIENT_ID") or infra.get("VITE_KC_CLIENT_ID") or "delpi-central"
    adm = admin_token(base, infra["KEYCLOAK_ADMIN"], infra["KEYCLOAK_ADMIN_PASSWORD"])
    admin_email = (
        infra.get("LNF_BOOTSTRAP_ADMIN_USERNAME")
        or infra.get("INITIAL_SUPERADMIN_EMAIL")
        or "user@local.com"
    )

    passwords: dict[str, str] = {}
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                passwords[key] = value

    bootstrap_password = ensure_bootstrap_admin(
        base, realm, adm, passwords, email=admin_email
    )
    admin_jwt = password_token(base, realm, client_id, admin_email, bootstrap_password)
    admin_me = me(core, admin_jwt)
    if not (admin_me.get("isSuperadmin") or admin_me.get("is_superadmin")):
        raise Fail(f"{admin_email} não é superadmin no Core do alvo")

    print("[setup] registrando manifesto LNF no Core")
    register_manifest(core, admin_jwt)
    perm_map = list_permissions(core, admin_jwt)
    missing = [
        code
        for code in {
            "lancamento-notas-fiscais.access",
            "lancamento-notas-fiscais.create",
            "lancamento-notas-fiscais.view",
            "lancamento-notas-fiscais.view.filial-01",
            "lancamento-notas-fiscais.view.filial-02",
            "lancamento-notas-fiscais.process",
            "lancamento-notas-fiscais.manage",
            "lancamento-notas-fiscais.review-unmapped-products",
        }
        if code not in perm_map
    ]
    if missing:
        raise Fail(f"permissions ausentes após register: {missing}")
    print(f"[setup] permissions LNF OK ({len(perm_map)} no catálogo com prefixo)")

    out_env = {
        "LNF_BASE_URL": f"{base}/apps/api-delpi",
        "LNF_TARGET": "api-delpi",
        "LNF_CORE_BASE_URL": core,
        "LNF_BOOTSTRAP_ADMIN_USERNAME": admin_email,
        "LNF_BOOTSTRAP_ADMIN_PASSWORD": bootstrap_password,
        "API_DELPI_INTERNAL_SERVICE_TOKEN": infra.get("API_DELPI_INTERNAL_SERVICE_TOKEN", ""),
        "LNF_TOKEN_P10": infra.get("API_DELPI_INTERNAL_SERVICE_TOKEN", ""),
        "LNF_ALLOW_RECONCILE_RUN": "1",
        "LNF_WRITE_GOLDEN": "1",
    }

    report: list[tuple[str, str, list[str], str]] = []
    for profile, meta in PROFILES.items():
        username = meta["username"]
        password = passwords.get(f"LNF_PASSWORD_{profile}") or gen_password()
        print(f"[setup] usuário {username}")
        ensure_kc_user(base, realm, adm, username, password)
        user_jwt = password_token(base, realm, client_id, username, password)
        user_me = me(core, user_jwt)
        user_id = str(user_me.get("id") or "")
        if not user_id:
            raise Fail(f"/me sem id para {username}")
        role_name = f"lnf-contract-{profile.lower()}"
        permission_codes = list(meta.get("permissions") or [])
        permission_ids: list[str] = []
        for code in permission_codes:
            pid = perm_map.get(code)
            if not pid:
                raise Fail(f"permission {code} ausente para {profile}")
            permission_ids.append(pid)
        role_id = ensure_role(core, admin_jwt, role_name, permission_ids)
        ensure_user_roles(core, admin_jwt, user_id, [role_id], superadmin=bool(meta["superadmin"]))
        # refresh /me after role change
        user_jwt = password_token(base, realm, client_id, username, password)
        user_me = me(core, user_jwt)
        effective = sorted(lnf_perms(user_me))
        is_super = bool(user_me.get("isSuperadmin") or user_me.get("is_superadmin"))
        if profile == "P9":
            ok = is_super
            expected = "superadmin"
        else:
            ok = set(effective) == EXPECTED_LNF[profile] and not is_super
            expected = ",".join(sorted(EXPECTED_LNF[profile])) or "(nenhuma LNF)"
        status = "OK" if ok else "DIVERGENTE"
        report.append((profile, username, effective, status))
        if not ok:
            print(f"[setup] DIVERGÊNCIA {profile}: esperado={expected} obtido={effective} super={is_super}")
        out_env[f"LNF_PASSWORD_{profile}"] = password
        out_env[f"LNF_TOKEN_{profile}"] = user_jwt
        out_env[f"LNF_USER_{profile}"] = username

    write_env_local(out_env)
    print("[setup] .env.local atualizado (gitignored)")
    print("perfil | login | permissions LNF | status")
    for profile, username, effective, status in report:
        print(f"{profile} | {username} | {effective or ['(nenhuma)']} | {status}")
    if any(status != "OK" for *_, status in report):
        raise Fail("há perfis com permissions divergentes; corrija antes da suíte")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Fail as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
