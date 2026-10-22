#!/usr/bin/env python3
"""Keycloak provisioner for the external-data-api S2S audience (prod-safe).

Bounded companion to the SHARED-INTEGRATIONS-01/X3 contract: ensures the
confidential client ``supplies-api`` carries an ``oidc-audience-mapper``
protocol mapper so its Client Credentials token lands ``external-data-api``
in the ``aud`` claim — required by the callee's ``S2S_AUDIENCE`` check
(``delpi_auth`` validator → 401 otherwise). The existing
``audience-api-delpi`` mapper is preserved untouched (additive only).

Safety rails (same convention as keycloak_s2s_supplies_scope.py):

  * DEFAULT MODE = --check (read-only drift report; modifies nothing);
  * realm and the ``supplies-api`` client must ALREADY exist — they are
    never created here (fail closed);
  * no user creation, no secret rotation/print, no realm mutation beyond
    the single audience protocol mapper;
  * --apply requires an https:// Keycloak base URL.

Usage:
    python3 infra/scripts/keycloak_s2s_external_data_audience.py          # check
    python3 infra/scripts/keycloak_s2s_external_data_audience.py --apply  # bounded apply

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
TARGET_AUDIENCE = "external-data-api"
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
        for line in _INFRA_ENV.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return ""


class KcAdmin:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.token = token

    def call(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"{self.base}{path}", data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("User-Agent", _USER_AGENT)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
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
        raise SystemExit("[ERRO] --apply exige base https:// em produção")

    realm = os.environ.get("KEYCLOAK_REALM") or REALM
    print(
        f"[kc-s2s-external-data] mode={'APPLY' if apply_mode else 'CHECK'} "
        f"realm={realm} base={base}"
    )
    admin = KcAdmin(base, mint_admin_token(base))

    # --- caller client must exist (creation out of scope) ---
    clients = admin.call(
        "GET", f"/admin/realms/{realm}/clients?clientId={CALLER_CLIENT}"
    )
    if not clients:
        report(
            False,
            "client supplies-api",
            "inexistente — provisionar conforme P1.SEC antes deste script",
        )
        return 1
    client = clients[0]
    client_uuid = client["id"]
    report(
        bool(client.get("serviceAccountsEnabled")),
        "client supplies-api",
        "service account habilitada"
        if client.get("serviceAccountsEnabled")
        else "serviceAccountsEnabled=false — recriar conforme P1.SEC",
    )

    # --- audience mapper for external-data-api (additive; api-delpi kept) ---
    mappers = (
        admin.call(
            "GET",
            f"/admin/realms/{realm}/clients/{client_uuid}"
            "/protocol-mappers/models",
        )
        or []
    )
    has_aud = any(
        m.get("protocolMapper") == "oidc-audience-mapper"
        and TARGET_AUDIENCE
        in str(m.get("config", {}).get("included.custom.audience", ""))
        + str(m.get("config", {}).get("included.client.audience", ""))
        for m in mappers
    )
    has_api_delpi = any(
        m.get("protocolMapper") == "oidc-audience-mapper"
        and "api-delpi"
        in str(m.get("config", {}).get("included.custom.audience", ""))
        + str(m.get("config", {}).get("included.client.audience", ""))
        for m in mappers
    )
    report(
        has_api_delpi,
        "audience mapper api-delpi",
        "presente (preservado)"
        if has_api_delpi
        else "ausente — integração api-delpi em risco; NÃO corrigir aqui",
    )
    if has_aud:
        report(True, "audience mapper external-data-api", "presente no cliente")
    elif not apply_mode:
        report(
            False,
            "audience mapper external-data-api",
            "ausente — aud!=external-data-api nega como 401; execute --apply",
        )
    else:
        admin.call(
            "POST",
            f"/admin/realms/{realm}/clients/{client_uuid}"
            "/protocol-mappers/models",
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
        report(True, "audience mapper external-data-api", "criado")

    return 0


if __name__ == "__main__":
    sys.exit(main())
