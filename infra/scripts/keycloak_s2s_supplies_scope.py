#!/usr/bin/env python3
"""Keycloak provisioner for the supplies S2S scopes (prod-safe).

Bounded companion to the P1.SEC S2S contract: ensures the confidential
client ``supplies-api`` carries the ``suppliers.read`` client scope as a
DEFAULT scope so the Client Credentials token lands the scope claim that
``api-delpi`` requires on ``GET /supplies/suppliers`` (``S2S_SCOPE_DENIED``
otherwise — observed as HTTP 403 in production).

Safety rails (same convention as keycloak-prod-delia-mcp-provision.sh):

  * DEFAULT MODE = --check (read-only drift report; modifies nothing);
  * realm and the ``supplies-api`` client must ALREADY exist — they are
    never created here (fail closed);
  * no user creation, no secret rotation/print, no realm mutation beyond
    the single client scope + default-scope assignment;
  * --apply requires an https:// Keycloak base URL.

Usage:
    python3 infra/scripts/keycloak_s2s_supplies_scope.py          # check
    python3 infra/scripts/keycloak_s2s_supplies_scope.py --apply  # bounded apply

Environment (read from infra/.env unless already set):
    KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD  — or KC_ADMIN_TOKEN
    KC_BASE_URL / KEYCLOAK_URL                — e.g. https://host/auth
    KEYCLOAK_REALM                            — defaults to delpi
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REALM = os.environ.get("KEYCLOAK_REALM", "delpi")
CALLER_CLIENT = "supplies-api"
TARGET_AUDIENCE = "api-delpi"
# api-delpi exige um scope por operação (protheus_router.py):
#   GET /integrations/protheus/suppliers -> suppliers.read
#   POST -> suppliers.create | PUT -> suppliers.update
#   GET /supplies/consumption-audit/orders/* -> consumption-audit.read
#     (GLPI #1353 — auditoria de consumo OP × operação, read-only)
# F3.4: S2S_SCOPE_DENIED no PUT porque só suppliers.read era provisionado.
REQUIRED_SCOPES = (
    "suppliers.read",
    "suppliers.create",
    "suppliers.update",
    "consumption-audit.read",
)
AUDIENCE_MAPPER_NAME = f"audience-{TARGET_AUDIENCE}"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

_INFRA_ENV = Path(__file__).resolve().parents[1] / ".env"


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    apply_mode = args.apply and not args.check

    base = _env_value("KC_BASE_URL") or _env_value("KEYCLOAK_URL")
    if not base:
        raise SystemExit("[ERRO] KC_BASE_URL/KEYCLOAK_URL ausente")
    if apply_mode and not base.startswith("https://"):
        if os.environ.get("KC_ALLOW_HTTP_APPLY") != "1":
            raise SystemExit(
                "[ERRO] --apply exige base https:// — para realm local de "
                "dev, exporte KC_ALLOW_HTTP_APPLY=1 explicitamente"
            )

    realm = os.environ.get("KEYCLOAK_REALM") or REALM
    print(f"[kc-s2s-supplies] mode={'APPLY' if apply_mode else 'CHECK'} "
          f"realm={realm} base={base}")
    admin = KcAdmin(base, mint_admin_token(base))

    # --- caller client: strict S2S shape, created only under --apply ---
    clients = admin.call(
        "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
    )
    if not clients:
        if not apply_mode:
            report(False, "client supplies-api", "inexistente — execute "
                   "--apply para criar (confidencial, service account, "
                   "somente client_credentials)")
            return 1
        admin.call(
            "POST", f"/admin/realms/{realm}/clients",
            {
                "clientId": CALLER_CLIENT,
                "protocol": "openid-connect",
                "enabled": True,
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "implicitFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "authorizationServicesEnabled": False,
            },
        )
        clients = admin.call(
            "GET",
            f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}",
        ) or []
        report(bool(clients), "client supplies-api",
               "criado (confidencial, SA, sem grants interativos)"
               if clients else "falha ao criar")
        if not clients:
            return 1
    client = clients[0]
    client_uuid = client["id"]
    report(
        bool(client.get("serviceAccountsEnabled")),
        "client supplies-api",
        "service account habilitada"
        if client.get("serviceAccountsEnabled")
        else "serviceAccountsEnabled=false — recriar conforme P1.SEC.5",
    )

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

    # --- secret handling: written to gitignored env, never printed ---
    if apply_mode:
        secret_body = admin.call(
            "GET",
            f"/admin/realms/{realm}/clients/{client_uuid}/client-secret",
        ) or {}
        secret = str(secret_body.get("value") or "")
        if secret:
            _write_env_config(secret)
        else:
            report(False, "client secret", "não retornado pelo Keycloak — "
                   "verificar serviceAccountsEnabled")
            return 1

    return 0


def _upsert_env(lines: list[str], key: str, value: str) -> list[str]:
    """Replace or append ``key=value`` in an env file line list."""
    prefix = f"{key}="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
            return lines
    lines.append(f"{key}={value}")
    return lines


def _write_env_config(secret: str) -> None:
    """Persist S2S_CLIENT_* into infra/.env.

    The secret value is written to the gitignored env file only — never
    to stdout, logs or the repository.
    """
    lines = (
        _INFRA_ENV.read_text(encoding="utf-8").splitlines()
        if _INFRA_ENV.is_file()
        else []
    )
    lines = _upsert_env(lines, "S2S_CLIENT_ID", CALLER_CLIENT)
    lines = _upsert_env(lines, "S2S_CLIENT_SECRET", secret)
    _INFRA_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report(True, "infra/.env", "S2S_CLIENT_ID/SECRET gravados "
           "(valores nunca exibidos)")


if __name__ == "__main__":
    sys.exit(main())
