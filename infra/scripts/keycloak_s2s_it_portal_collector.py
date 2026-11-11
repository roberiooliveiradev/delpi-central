#!/usr/bin/env python3
"""Keycloak provisioner for the IT Portal Linux host collector (E4.S1).

Ensures the confidential client ``it-portal-host-collector`` exists with
service-account client_credentials only, carries
``it-portal.observations.ingest`` as a DEFAULT client scope, and maps
audience ``it-portal-api`` into the access token.

Safety rails:

  * DEFAULT MODE = --check (read-only drift report; modifies nothing);
  * realm must ALREADY exist — never created here;
  * --apply creates/updates ONLY this bounded client + scope + audience mapper;
  * no user creation, no secret print/log;
  * --apply requires https:// Keycloak base URL unless KC_ALLOW_HTTP_APPLY=1.

Companion env (it-portal-api):
    S2S_AUDIENCE=it-portal-api
    S2S_ALLOWED_CLIENTS=it-portal-host-collector
    IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST=<uuid-do-srv-api>

Usage:
    python3 infra/scripts/keycloak_s2s_it_portal_collector.py
    python3 infra/scripts/keycloak_s2s_it_portal_collector.py --apply
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
CALLER_CLIENT = "it-portal-host-collector"
TARGET_AUDIENCE = "it-portal-api"
REQUIRED_SCOPES = ("it-portal.observations.ingest",)
AUDIENCE_MAPPER_NAME = f"audience-{TARGET_AUDIENCE}"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
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
        req.add_header("User-Agent", _USER_AGENT)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                return json.loads(raw) if raw.strip() else None
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409):
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


def _write_env_hints(secret: str) -> None:
    """Escreve placeholders/secret no infra/.env sem imprimir o secret."""
    if not _INFRA_ENV.exists():
        report(False, "infra/.env", "arquivo ausente — secret não persistido")
        return
    text = _INFRA_ENV.read_text(encoding="utf-8")
    updates = {
        "IT_PORTAL_S2S_AUDIENCE": TARGET_AUDIENCE,
        "IT_PORTAL_S2S_ALLOWED_CLIENTS": CALLER_CLIENT,
        "IT_PORTAL_COLLECTOR_S2S_CLIENT_ID": CALLER_CLIENT,
        "IT_PORTAL_COLLECTOR_S2S_CLIENT_SECRET": secret,
        "IT_PORTAL_COLLECTOR_S2S_SCOPE": " ".join(REQUIRED_SCOPES),
    }
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
    _INFRA_ENV.write_text("".join(out), encoding="utf-8")
    report(True, "infra/.env", "IT_PORTAL_* S2S atualizado (secret não exibido)")


def run(*, apply_mode: bool) -> int:
    base = _keycloak_base()
    if not base:
        raise SystemExit("[ERRO] KEYCLOAK_URL/KC_BASE_URL ausente")
    if apply_mode and not base.startswith("https://") and os.environ.get("KC_ALLOW_HTTP_APPLY") != "1":
        raise SystemExit(
            "[ERRO] --apply exige https:// Keycloak (ou KC_ALLOW_HTTP_APPLY=1 em lab)"
        )

    print(f"Keycloak S2S IT Portal collector ({'APPLY' if apply_mode else 'CHECK'})")
    print(f"  base={base} realm={REALM} client={CALLER_CLIENT}")

    admin = KcAdmin(base, mint_admin_token(base))
    realm = REALM

    clients = admin.call(
        "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
    )
    if not clients:
        if not apply_mode:
            report(
                False,
                f"client {CALLER_CLIENT}",
                "inexistente — execute --apply para criar (confidencial, SA)",
            )
            print(
                "\n[REMINDER] it-portal-api env: "
                "S2S_AUDIENCE=it-portal-api "
                "S2S_ALLOWED_CLIENTS=it-portal-host-collector"
            )
            return 1
        admin.call(
            "POST",
            f"/admin/realms/{realm}/clients",
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
            "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
        ) or []
        report(bool(clients), f"client {CALLER_CLIENT}", "criado" if clients else "falha")
        if not clients:
            return 1

    client = clients[0]
    client_uuid = client["id"]
    report(
        bool(client.get("serviceAccountsEnabled")),
        f"client {CALLER_CLIENT}",
        "service account habilitada"
        if client.get("serviceAccountsEnabled")
        else "serviceAccountsEnabled=false",
    )

    assigned = admin.call(
        "GET",
        f"/admin/realms/{realm}/clients/{client_uuid}/default-client-scopes",
    ) or []
    for required_scope in REQUIRED_SCOPES:
        scopes = admin.call("GET", f"/admin/realms/{realm}/client-scopes") or []
        scope = next((s for s in scopes if s.get("name") == required_scope), None)
        scope_id = None
        if scope is None:
            if not apply_mode:
                report(False, f"client scope {required_scope}", "ausente — --apply")
            else:
                admin.call(
                    "POST",
                    f"/admin/realms/{realm}/client-scopes",
                    {
                        "name": required_scope,
                        "protocol": "openid-connect",
                        "attributes": {"include.in.token.scope": "true"},
                    },
                )
                scopes = admin.call("GET", f"/admin/realms/{realm}/client-scopes") or []
                scope = next((s for s in scopes if s.get("name") == required_scope), None)
                scope_id = scope["id"] if scope else None
                report(bool(scope_id), f"client scope {required_scope}", "criado" if scope_id else "falha")
        else:
            scope_id = scope["id"]
            report(True, f"client scope {required_scope}", "presente")

        if not scope_id:
            continue
        is_default = any(s.get("id") == scope_id for s in assigned)
        if is_default:
            report(True, f"default scope {required_scope}", "atribuído")
        elif not apply_mode:
            report(False, f"default scope {required_scope}", "não atribuído — --apply")
        else:
            admin.call(
                "PUT",
                f"/admin/realms/{realm}/clients/{client_uuid}/default-client-scopes/{scope_id}",
            )
            report(True, f"default scope {required_scope}", "atribuído")

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
        report(True, f"audience mapper {TARGET_AUDIENCE}", "presente")
    elif not apply_mode:
        report(False, f"audience mapper {TARGET_AUDIENCE}", "ausente — --apply")
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
        report(True, f"audience mapper {TARGET_AUDIENCE}", "criado")

    if apply_mode:
        secret_body = admin.call(
            "GET",
            f"/admin/realms/{realm}/clients/{client_uuid}/client-secret",
        ) or {}
        secret = str(secret_body.get("value") or "")
        if secret:
            _write_env_hints(secret)
        else:
            report(False, "client secret", "não retornado pelo Keycloak")

    print(
        "\n[REMINDER] Compose it-portal-api: "
        "S2S_AUDIENCE=it-portal-api S2S_ALLOWED_CLIENTS=it-portal-host-collector "
        "+ IT_PORTAL_COLLECTOR_SERVER_ALLOWLIST=<uuid>"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica mudanças bounded (default = --check somente leitura).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Modo explícito de verificação (default).",
    )
    args = parser.parse_args()
    apply_mode = bool(args.apply) and not args.check
    return run(apply_mode=apply_mode)


if __name__ == "__main__":
    sys.exit(main())
