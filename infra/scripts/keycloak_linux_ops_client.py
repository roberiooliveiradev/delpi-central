#!/usr/bin/env python3
"""Bounded Keycloak client bootstrap for the read-only Linux Ops MCP.

Default --check: GET only. --apply requires an exact ChatGPT redirect
URI copied from the connector UI. Creates/links ONLY mcp-linux-ops and
its dedicated audience scope; never changes the shared mcp:tools scope,
Portal clients, other MCP clients, users, realm, token exchange or secrets.

Operator run on srv-api only. NO printing of access tokens or client secrets.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from delia_mcp_keycloak_state import (
    KcAdmin, ProvisioningError, mint_admin_token, server_version,
)

CLIENT = "mcp-linux-ops"
DEDICATED_SCOPE = "mcp-audience-linux-ops"
DEFAULT_SCOPE_NAMES = ("mcp:tools", "audience-delpi", "profile", "email")
CLIENT_FLAGS = {
    "enabled": True,
    "publicClient": False,
    "standardFlowEnabled": True,
    "implicitFlowEnabled": False,
    "directAccessGrantsEnabled": False,
    "serviceAccountsEnabled": False,
}
MAPPER_NAME = "linux-ops-resource-audience"
RESOURCE_SUFFIX = "/apps/linux-ops-mcp/mcp"
# ChatGPT supplies the exact redirect URI in its connector registration UI.
# Only allow a strongly constrained HTTPS callback host, without wildcard.
ALLOWED_CALLBACK_HOSTS = frozenset({"chatgpt.com", "chat.openai.com"})


class ContractError(Exception):
    """No credential, admin body or token detail is printed for these failures."""


def _read_env_file() -> dict[str, str]:
    p = Path(__file__).resolve().parents[1] / ".env"
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip("'\"")
    return out


def _value(name: str, envfile: dict[str, str]) -> str:
    return (os.environ.get(name) or envfile.get(name) or "").strip()


def valid_callback(raw: str) -> bool:
    if not isinstance(raw, str) or not raw or len(raw) > 500:
        return False
    p = urlparse(raw)
    return bool(
        p.scheme == "https"
        and p.hostname in ALLOWED_CALLBACK_HOSTS
        and p.port is None
        and not p.username and not p.password
        and p.path.startswith("/")
        and p.path not in ("/", "")
        and not p.query and not p.fragment
        and "*" not in raw
        and raw == p.geturl()
    )


def strict_resource(base: str, resource: str) -> str:
    b, r = urlparse(base), urlparse(resource)
    if (
        b.scheme != "https"
        or not b.netloc
        or b.username or b.password
        or b.path not in ("", "/") or b.query or b.fragment
        or r.scheme != "https"
        or r.netloc != b.netloc
        or r.path != RESOURCE_SUFFIX
        or r.username or r.password or r.query or r.fragment
        or resource != base.rstrip("/") + RESOURCE_SUFFIX
    ):
        raise ContractError("public base/resource mismatch; no mutation")
    return resource


@dataclass(frozen=True)
class Config:
    kc_base: str
    realm: str
    resource: str
    callback: str

    @classmethod
    def from_env(cls) -> "Config":
        env = _read_env_file()
        base = _value("PUBLIC_BASE_URL", env).rstrip("/")
        resource = strict_resource(
            base, _value("LINUX_OPS_MCP_RESOURCE_URL", env))
        kc_base = (
            _value("KC_BASE_URL", env)
            or _value("KEYCLOAK_URL", env)
            or base + "/auth"
        ).rstrip("/")
        parsed = urlparse(kc_base)
        if (
            parsed.scheme != "https" or not parsed.netloc
            or parsed.username or parsed.password
            or parsed.query or parsed.fragment
            or parsed.path != "/auth"
        ):
            raise ContractError("Keycloak admin endpoint must be an HTTPS /auth URL")
        realm = _value("KEYCLOAK_REALM", env) or "delpi"
        if realm != "delpi":
            raise ContractError("wrong realm; expected delpi")
        cb = _value("LINUX_OPS_OAUTH_REDIRECT_URI", env)
        if cb and not valid_callback(cb):
            raise ContractError("invalid ChatGPT redirect; use exact UI callback")
        return cls(kc_base, realm, resource, cb)


class Provisioner:
    """Least-change converge; unknown preexisting state fails closed."""

    def __init__(self, admin: KcAdmin, cfg: Config):
        self.a, self.c = admin, cfg

    def _p(self, suffix: str) -> str:
        return f"/realms/{self.c.realm}/{suffix}"

    def _get(self, suffix: str):
        return self.a.call("GET", self._p(suffix))[1]

    def _clients(self):
        from urllib.parse import quote
        rows = self._get(f"clients?clientId={quote(CLIENT, safe='')}") or []
        return [x for x in rows if x.get("clientId") == CLIENT]

    def _uuid(self) -> str:
        rows = self._clients()
        if len(rows) > 1:
            raise ContractError("duplicate target clients; manual review")
        return rows[0]["id"] if rows else ""

    def _scopes(self):
        rows = self._get("client-scopes") or []
        return {s["name"]: s for s in rows}

    def _mappers(self, scope_id: str):
        return self._get(f"client-scopes/{scope_id}/protocol-mappers/models") or []

    def _defaults(self, client_uuid: str):
        rows = self._get(f"clients/{client_uuid}/default-client-scopes") or []
        return {s["id"] for s in rows}

    def _audience_mapper_valid(self, scope: dict, audience: str) -> bool:
        """Require the approved value in access-token aud, not just scope existence."""
        mappers = self._mappers(scope["id"])
        return any(
            m.get("protocolMapper") == "oidc-audience-mapper"
            and (
                cfg.get("included.custom.audience") == audience
                or cfg.get("included.client.audience") == audience
            )
            and cfg.get("access.token.claim") == "true"
            for m in mappers
            for cfg in [m.get("config") or {}]
        )

    def _dedicated_mapper_status(self, scope: dict) -> str | None:
        """Detect scope drift before creating a client or making any write."""
        mappers = self._mappers(scope["id"])
        if not mappers:
            return "absent"
        valid = [
            m for m in mappers
            if m.get("protocolMapper") == "oidc-audience-mapper"
            and m.get("config", {}).get("included.custom.audience") == self.c.resource
            and m.get("config", {}).get("access.token.claim") == "true"
        ]
        return None if len(valid) == 1 and len(mappers) == 1 else "unexpected"

    def audit(self) -> list[str]:
        """Read-only drift; never returns raw client repr, tokens or credentials."""
        issues = []
        realm = self.a.call("GET", f"/realms/{self.c.realm}", tolerate=(404,))[0]
        if realm == 404:
            raise ContractError("realm delpi absent")
        scopes = self._scopes()
        for name in DEFAULT_SCOPE_NAMES:
            if name not in scopes:
                issues.append(f"required shared scope missing: {name}")
        shared_audience = scopes.get("audience-delpi")
        if shared_audience and not self._audience_mapper_valid(
            shared_audience, "delpi-central"
        ):
            issues.append("shared platform audience mapper missing or invalid")
        audience_scope = scopes.get(DEDICATED_SCOPE)
        if audience_scope:
            if self._dedicated_mapper_status(audience_scope) is not None:
                issues.append("dedicated scope audience mapper differs")
        else:
            issues.append("dedicated audience scope absent")
        uuid = self._uuid()
        if not uuid:
            issues.append("dedicated OAuth client absent")
            return issues
        full = self._get(f"clients/{uuid}")
        for key, expected in CLIENT_FLAGS.items():
            if full.get(key) != expected:
                issues.append(f"client flag mismatch: {key}")
        if (full.get("attributes") or {}).get("pkce.code.challenge.method") != "S256":
            issues.append("client PKCE must be S256")
        if full.get("clientAuthenticatorType") not in ("client-secret", None):
            issues.append("unexpected client authenticator")
        redirects = full.get("redirectUris") or []
        if len(redirects) != 1 or not valid_callback(redirects[0]):
            issues.append("redirect URI must be one exact ChatGPT callback")
        if self.c.callback and redirects != [self.c.callback]:
            issues.append("redirect URI differs from requested callback")
        if full.get("webOrigins") not in ([], None):
            issues.append("web origins must be empty")
        defaults = self._defaults(uuid)
        for name in DEFAULT_SCOPE_NAMES + (DEDICATED_SCOPE,):
            scope = scopes.get(name)
            if scope and scope["id"] not in defaults:
                issues.append(f"default scope not assigned: {name}")
        return issues

    def apply(self) -> None:
        """Only new client/scope + assignments to that client, no other writes."""
        if not valid_callback(self.c.callback):
            raise ContractError("exact callback required before --apply")
        scopes = self._scopes()
        for name in DEFAULT_SCOPE_NAMES:
            if name not in scopes:
                raise ContractError(f"shared scope missing; do not create: {name}")
        if not self._audience_mapper_valid(scopes["audience-delpi"], "delpi-central"):
            raise ContractError("shared platform audience mapper missing or invalid")
        # Preflight ALL existing shared/dedicated mapper state before first write.
        # A conflicting resource mapper must never leave a newly created client.
        existing_scope = scopes.get(DEDICATED_SCOPE)
        if existing_scope and self._dedicated_mapper_status(existing_scope) == "unexpected":
            raise ContractError("unexpected mapper in dedicated scope")

        uuid = self._uuid()
        if uuid:
            existing = self._get(f"clients/{uuid}")
            # Existing client must be manually reviewed on any drift;
            # never override an unknown redirect or reconfigure its flows.
            for key, expected in CLIENT_FLAGS.items():
                if existing.get(key) != expected:
                    raise ContractError(f"existing client mismatched: {key}")
            if (existing.get("attributes") or {}).get("pkce.code.challenge.method") != "S256":
                raise ContractError("existing client PKCE drift")
            if existing.get("redirectUris") != [self.c.callback]:
                raise ContractError("existing client callback drift")
            if existing.get("webOrigins") not in ([], None):
                raise ContractError("existing client CORS drift")
        else:
            body = {
                "clientId": CLIENT, "protocol": "openid-connect",
                "clientAuthenticatorType": "client-secret",
                "redirectUris": [self.c.callback],
                "webOrigins": [],
                "attributes": {"pkce.code.challenge.method": "S256"},
                **CLIENT_FLAGS,
            }
            self.a.call("POST", self._p("clients"), body)
            uuid = self._uuid()
            if not uuid:
                raise ContractError("client creation not verified")

        scope = scopes.get(DEDICATED_SCOPE)
        if not scope:
            self.a.call("POST", self._p("client-scopes"), {
                "name": DEDICATED_SCOPE,
                "protocol": "openid-connect",
                "attributes": {"include.in.token.scope": "false"},
            })
            scope = self._scopes().get(DEDICATED_SCOPE)
            if not scope:
                raise ContractError("dedicated scope creation not verified")
        mappers = self._mappers(scope["id"])
        expected = [m for m in mappers if
                    m.get("protocolMapper") == "oidc-audience-mapper"
                    and m.get("config", {}).get("included.custom.audience") == self.c.resource
                    and m.get("config", {}).get("access.token.claim") == "true"]
        if not mappers:
            self.a.call("POST",
                self._p(f"client-scopes/{scope['id']}/protocol-mappers/models"), {
                    "name": MAPPER_NAME,
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-audience-mapper",
                    "config": {
                        "included.custom.audience": self.c.resource,
                        "access.token.claim": "true",
                        "id.token.claim": "false",
                    },
                })
        elif len(mappers) != 1 or len(expected) != 1:
            raise ContractError("unexpected mapper in dedicated scope")

        defaults = self._defaults(uuid)
        scopes = self._scopes()
        for name in DEFAULT_SCOPE_NAMES + (DEDICATED_SCOPE,):
            scope_id = scopes[name]["id"]
            if scope_id not in defaults:
                self.a.call("PUT",
                    self._p(f"clients/{uuid}/default-client-scopes/{scope_id}"))
        issues = self.audit()
        if issues:
            raise ContractError("post-apply audit incomplete: " + "; ".join(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="read-only Keycloak state check (default)")
    mode.add_argument("--apply", action="store_true",
                      help="bounded creation; requires exact callback in local env")
    args = parser.parse_args()
    try:
        cfg = Config.from_env()
        env = _read_env_file()
        token = _value("KC_ADMIN_TOKEN", env)
        if not token:
            user = _value("KEYCLOAK_ADMIN", env)
            pw = _value("KEYCLOAK_ADMIN_PASSWORD", env)
            if not user or not pw:
                raise ContractError("Keycloak admin credentials missing on host")
            token = mint_admin_token(cfg.kc_base, user, pw)
        version = server_version(cfg.kc_base, token)
        if not version.startswith("24."):
            raise ContractError("running Keycloak differs from pinned 24.x; review")
        admin = KcAdmin(cfg.kc_base, token)
        prov = Provisioner(admin, cfg)
        if args.apply:
            prov.apply()
        issues = prov.audit()
        print("[linux-ops-keycloak] client=mcp-linux-ops", 
              "mode=APPLY" if args.apply else "mode=CHECK")
        for issue in issues:
            print("[DRIFT]", issue)
        if issues:
            return 2
        print("[linux-ops-keycloak] NO_DRIFT")
        return 0
    except (ContractError, ProvisioningError, KeyError, ValueError) as exc:
        # The lower-level API may include response bodies; keep logs safe.
        message = str(exc) if isinstance(exc, ContractError) else type(exc).__name__
        print("[linux-ops-keycloak] FAIL_CLOSED:", message, file=sys.stderr)
        return 1
    except Exception:
        print("[linux-ops-keycloak] FAIL_CLOSED: unexpected error", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
