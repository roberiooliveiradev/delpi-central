#!/usr/bin/env python3
"""Keycloak provisioner for the TV Helpdesk summary S2S scope (prod-safe).

Ensures the existing confidential client ``tv-dashboard-api`` carries
``helpdesk.dashboard.read`` as a DEFAULT scope and an ``api-delpi`` audience
mapper. The client is never created here. Default mode is read-only.

Safety rails:

  * DEFAULT MODE = --check (modifies nothing);
  * realm and ``tv-dashboard-api`` must already exist;
  * no user creation, no secret rotation or print;
  * --apply requires an https:// Keycloak base URL and explicit ops approval.

Usage:
    python3 infra/scripts/keycloak_s2s_tv_dashboard_helpdesk_scope.py
    python3 infra/scripts/keycloak_s2s_tv_dashboard_helpdesk_scope.py --apply

Environment (read from infra/.env unless already set):
    KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD  — or KC_ADMIN_TOKEN
    KC_BASE_URL / KEYCLOAK_URL                — e.g. https://host/auth
    KEYCLOAK_REALM                            — defaults to delpi
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REALM = os.environ.get("KEYCLOAK_REALM", "delpi")
CALLER_CLIENT = "tv-dashboard-api"
TARGET_AUDIENCE = "api-delpi"
REQUIRED_SCOPES = ("helpdesk.dashboard.read",)
AUDIENCE_MAPPER_NAME = f"audience-{TARGET_AUDIENCE}"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

_INFRA_ENV = Path(__file__).resolve().parents[1] / ".env"


def _keycloak_base() -> str:
    for key in ("KC_BASE_URL", "KEYCLOAK_URL"):
        value = _env_value(key)
        if value.startswith("http"):
            return value.rstrip("/")
    for key in ("S2S_TOKEN_URL", "KEYCLOAK_ISSUER", "KEYCLOAK_JWKS_URL"):
        value = _env_value(key)
        marker = "/realms/"
        if value.startswith("http") and marker in value:
            return value.split(marker, 1)[0].rstrip("/")
    return ""


def _env_value(key: str) -> str:
    value = os.environ.get(key)
    if value:
        return value
    if _INFRA_ENV.is_file():
        for line in _INFRA_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


class KcAdmin:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.token = token

    def call(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}", data=data, method=method,
        )
        req.add_header("Authorization", f"Bearer {self.token}")
        # Cloudflare WAF bans non-browser signatures (error 1010) on the
        # public /auth proxy; inside the docker network this is a no-op.
        req.add_header("User-Agent", _USER_AGENT)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                return json.loads(raw) if raw.strip() else None
        except urllib.error.HTTPError as exc:
            if exc.code == 409:  # resource already exists
                return None
            raise RuntimeError(
                f"{method} {path} -> HTTP {exc.code}: {exc.read()[:200]!r}"
            ) from exc


def mint_admin_token(base: str) -> str:
    token = _env_value("KC_ADMIN_TOKEN")
    if token:
        return token
    user = _env_value("KEYCLOAK_ADMIN")
    password = _env_value("KEYCLOAK_ADMIN_PASSWORD")
    if not user or not password:
        raise SystemExit(
            "[ERRO] sem KC_ADMIN_TOKEN nem KEYCLOAK_ADMIN/KEYCLOAK_ADMIN_PASSWORD"
        )
    data = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": user,
            "password": password,
        }
    ).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/realms/master/protocol/openid-connect/token",
        data=data,
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", _USER_AGENT)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["access_token"]


def report(ok: bool, element: str, note: str) -> None:
    tag = "OK    " if ok else "DRIFT "
    print(f"  [{tag}] {element} — {note}")


def _host_resolves(base: str) -> bool:
    host = urllib.parse.urlparse(base).hostname
    if not host:
        return False
    try:
        socket.getaddrinfo(host, None)
        return True
    except OSError:
        return False


def _update_env(path: Path, updates: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines(True) if text else []
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}\n")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}\n")
    path.write_text("".join(out), encoding="utf-8")


def _bridge_if_unresolved(apply_mode: bool) -> int | None:
    if os.environ.get("KC_DOCKER_BRIDGE") == "1":
        return None
    base = _keycloak_base()
    if not base or _host_resolves(base):
        return None
    payload = {
        "KC_BASE_URL": "http://keycloak:8080/auth",
        "KEYCLOAK_ADMIN": _env_value("KEYCLOAK_ADMIN"),
        "KEYCLOAK_ADMIN_PASSWORD": _env_value("KEYCLOAK_ADMIN_PASSWORD"),
        "KEYCLOAK_REALM": _env_value("KEYCLOAK_REALM") or REALM,
        "KC_DOCKER_BRIDGE": "1",
        "KC_APPLY": "1" if apply_mode else "0",
    }
    bootstrap = (
        "import json,os,sys\n"
        "cfg=json.loads(sys.stdin.readline())\n"
        "os.environ.update({k:str(v) for k,v in cfg.items() if v})\n"
        "sys.argv=['keycloak_s2s_tv_dashboard_helpdesk_scope.py']\n"
        "sys.argv.append('--apply' if os.environ.get('KC_APPLY')=='1' else '--check')\n"
        "src=sys.stdin.read()\n"
        "exec(compile(src,'keycloak_s2s_tv_dashboard_helpdesk_scope.py','exec'),"
        "{'__name__':'__main__','__file__':'/tmp/keycloak_s2s_tv_dashboard_helpdesk_scope.py'})\n"
    )
    source = Path(__file__).read_text(encoding="utf-8")
    proc = subprocess.run(
        ["docker", "exec", "-i", "delpi-helpdesk-api", "python3", "-c", bootstrap],
        input=(json.dumps(payload) + "\n" + source).encode(),
        capture_output=True,
    )
    secret = ""
    for raw in proc.stdout.decode(errors="replace").splitlines():
        if raw.startswith("SECRET_LINE="):
            secret = raw.split("=", 1)[1]
            continue
        print(raw)
    if proc.stderr:
        sys.stderr.write(proc.stderr.decode(errors="replace"))
    if secret:
        _update_env(_INFRA_ENV, {"TV_DASHBOARD_S2S_CLIENT_SECRET": secret})
        print("  [OK    ] client secret — gravado no ambiente, valor omitido")
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    apply_mode = args.apply and not args.check
    bridged = _bridge_if_unresolved(apply_mode)
    if bridged is not None:
        return bridged

    base = _keycloak_base()
    if not base:
        raise SystemExit("[ERRO] KC_BASE_URL/KEYCLOAK_URL ausente")
    internal = base.rstrip("/") == "http://keycloak:8080/auth"
    if apply_mode and not (base.startswith("https://") or internal):
        raise SystemExit("[ERRO] --apply exige base https:// ou o Keycloak interno do compose")

    realm = os.environ.get("KEYCLOAK_REALM") or REALM
    print(f"[kc-s2s-tv-helpdesk] mode={'APPLY' if apply_mode else 'CHECK'} "
          f"realm={realm} base={'internal' if internal else 'public'}")
    admin = KcAdmin(base, mint_admin_token(base))

    # --- caller client must exist (creation out of scope) ---
    clients = admin.call(
        "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
    )
    if not clients:
        if not apply_mode:
            report(False, "client tv-dashboard-api", "inexistente — --apply cria só o cliente confidencial")
            return 1
        admin.call(
            "POST",
            f"/admin/realms/{realm}/clients",
            {
                "clientId": CALLER_CLIENT,
                "protocol": "openid-connect",
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "implicitFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "clientAuthenticatorType": "client-secret",
            },
        )
        clients = admin.call(
            "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
        )
        if not clients:
            report(False, "client tv-dashboard-api", "falha ao criar")
            return 1
        report(True, "client tv-dashboard-api", "criado confidencial, sem fluxo de usuário")
    client = clients[0]
    client_uuid = client["id"]
    if not client.get("serviceAccountsEnabled"):
        if not apply_mode:
            report(False, "client tv-dashboard-api", "serviceAccountsEnabled=false")
            return 1
        client["serviceAccountsEnabled"] = True
        client["publicClient"] = False
        client["standardFlowEnabled"] = False
        client["directAccessGrantsEnabled"] = False
        admin.call(
            "PUT",
            f"/admin/realms/{realm}/clients/{client_uuid}",
            client,
        )
        report(True, "client tv-dashboard-api", "service account habilitada")
    else:
        report(True, "client tv-dashboard-api", "service account habilitada")

    # --- required scopes exist and are assigned as DEFAULT ---
    assigned = admin.call(
        "GET",
        f"/admin/realms/{realm}/clients/{client_uuid}/default-client-scopes",
    ) or []
    for required_scope in REQUIRED_SCOPES:
        scopes = admin.call("GET", f"/admin/realms/{realm}/client-scopes") or []
        scope = next(
            (s for s in scopes if s.get("name") == required_scope), None
        )
        scope_id = None
        if scope is None:
            if not apply_mode:
                report(False, f"client scope {required_scope}",
                       "ausente — execute --apply para criar e atribuir")
            else:
                admin.call(
                    "POST", f"/admin/realms/{realm}/client-scopes",
                    {
                        "name": required_scope,
                        "protocol": "openid-connect",
                        "attributes": {"include.in.token.scope": "true"},
                    },
                )
                scopes = (
                    admin.call("GET", f"/admin/realms/{realm}/client-scopes")
                    or []
                )
                scope = next(
                    (s for s in scopes if s.get("name") == required_scope),
                    None,
                )
                scope_id = scope["id"] if scope else None
                report(bool(scope_id), f"client scope {required_scope}",
                       "criado" if scope_id else "falha ao criar")
        else:
            scope_id = scope["id"]
            report(True, f"client scope {required_scope}", "presente")

        # --- DEFAULT assignment so tokens carry it without S2S_SCOPE ---
        if not scope_id:
            continue
        is_default = any(s.get("id") == scope_id for s in assigned)
        if is_default:
            report(True, f"default scope {required_scope}", "atribuído")
        elif not apply_mode:
            report(False, f"default scope {required_scope}",
                   "não atribuído — execute --apply")
        else:
            admin.call(
                "PUT",
                f"/admin/realms/{realm}/clients/{client_uuid}"
                f"/default-client-scopes/{scope_id}",
            )
            assigned = admin.call(
                "GET",
                f"/admin/realms/{realm}/clients/{client_uuid}"
                "/default-client-scopes",
            ) or []
            report(True, f"default scope {required_scope}", "atribuído")

    # --- audience mapper for api-delpi (evidência P1.SEC.5: já provisionado) ---
    mappers = admin.call(
        "GET",
        f"/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models",
    ) or []
    has_aud = any(
        m.get("protocolMapper") == "oidc-audience-mapper"
        and TARGET_AUDIENCE
        in str(m.get("config", {}).get("included.custom.audience", ""))
            + str(m.get("config", {}).get("included.client.audience", ""))
        for m in mappers
    )
    if has_aud:
        report(True, "audience mapper api-delpi", "presente no cliente")
    elif not apply_mode:
        report(False, "audience mapper api-delpi",
               "ausente — aud!=api-delpi nega como S2S_TOKEN_INVALID (401)")
    else:
        admin.call(
            "POST",
            f"/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models",
            {
                "name": AUDIENCE_MAPPER_NAME,
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "config": {
                    "id.token.claim": "false",
                    "access.token.claim": "true",
                    "included.custom.audience": TARGET_AUDIENCE,
                },
            },
        )
        report(True, "audience mapper api-delpi", "criado")

    if apply_mode:
        secret_doc = admin.call(
            "GET",
            f"/admin/realms/{realm}/clients/{client_uuid}/client-secret",
        ) or {}
        secret = str(secret_doc.get("value") or "").strip()
        if not secret:
            report(False, "client secret", "ausente")
            return 1
        if os.environ.get("KC_DOCKER_BRIDGE") == "1":
            print(f"SECRET_LINE={secret}")
        else:
            _update_env(_INFRA_ENV, {"TV_DASHBOARD_S2S_CLIENT_SECRET": secret})
            report(True, "client secret", "gravado no ambiente, valor omitido")

    return 0


if __name__ == "__main__":
    sys.exit(main())
