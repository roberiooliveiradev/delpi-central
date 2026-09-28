"""OAuth transport contract for MCP over HTTPS (OpenAI Plugin / FastMCP).

Same rules as JWT middleware for `/api/*`, but `/mcp` adds:
- RFC 9728 `WWW-Authenticate` + protected-resource metadata
- exact resource **audience** must appear in JWT `aud`
- generic scope `mcp:tools` (never include `audience-delpi` style resource id)
"""

from __future__ import annotations

import os
import urllib.parse

from tv_app.config import settings

from .constants import CANONICAL_MCP_RESOURCE_URL, MCP_GATEWAY_ROOT, MCP_PREDEFINED_CLIENT_ID

# Scopes the MCP confidential client must request (generic OAuth profile only).
MCP_CLIENT_SCOPES: tuple[str, ...] = ("openid", "profile", "email", "mcp:tools")

MCP_TOOL_SECURITY_SCHEMES: tuple[str, ...] = (
    "Authorization Code",
    "Bearer OAuth",
)


def resolve_predefined_mcp_client_id() -> str:
    return (os.environ.get("MCP_PREDEFINED_CLIENT_ID") or "").strip() or MCP_PREDEFINED_CLIENT_ID


def resolve_required_mcp_resource_audience() -> str:
    """Canonical `aud` required on Bearer for /mcp (must be exactly the MCP resource URL).

    Resolution order: explicit `MCP_RESOURCE_URL` override → `PUBLIC_BASE_URL`
    + public app root (`TV_DASHBOARD_API_ROOT_PATH`) + `/mcp` → canonical
    minhadelpi.com.br URL (docker-compose convention).
    """
    env_url = (os.environ.get("MCP_RESOURCE_URL") or "").strip()
    if env_url:
        return env_url
    base = (os.environ.get("PUBLIC_BASE_URL") or "").strip() or settings.PUBLIC_BASE_URL or ""
    if base:
        root = (settings.TV_DASHBOARD_API_ROOT_PATH or "").strip("/")
        return f"{base.rstrip('/')}/{root}/mcp" if root else f"{base.rstrip('/')}/mcp"
    return CANONICAL_MCP_RESOURCE_URL


def build_www_authenticate_challenge(*, include_mcp_tools_scope: bool = True) -> str:
    """RFC 6750 challenge for 401 on MCP JSON-RPC (RFC 9728 resource_metadata)."""
    from .resource_metadata import protected_resource_metadata_url

    resource = resolve_required_mcp_resource_audience()
    meta = protected_resource_metadata_url(resource)
    parts = [
        'Bearer realm="mcp"',
        f'resource_metadata="{meta}"',
        'error="invalid_token"',
        'error_description="Missing or invalid access token"',
    ]
    if include_mcp_tools_scope:
        parts.append('scope="mcp:tools"')
    return ", ".join(parts)


def _jwt_token_audiences_claims(payload: dict) -> set[str]:
    aud = payload.get("aud")
    if aud is None:
        return set()
    if isinstance(aud, str):
        return {aud}
    if isinstance(aud, list):
        return {str(x) for x in aud}
    return set()


def mcp_audience_satisfied(payload: dict) -> bool:
    """JWT `aud` must contain the exact MCP resource URL (not gateway root alone)."""
    expected = resolve_required_mcp_resource_audience()
    actual = _jwt_token_audiences_claims(payload)
    return bool(actual) and expected in actual


def _parse_jwt_scope_strings(payload: dict) -> list[str]:
    raw = payload.get("scope")
    if not isinstance(raw, str):
        return []
    return [s for s in raw.split() if s]


def mcp_required_scopes_satisfied(payload: dict) -> bool:
    """Generic OAuth scopes only — never product/resource client ids."""
    scopes = set(_parse_jwt_scope_strings(payload))
    return set(MCP_CLIENT_SCOPES).issubset(scopes)


def valid_oauth_client_id(value: str) -> bool:
    """Product docs show `mcp-tv-dashboard` even where callers used id `plugin` legacy."""
    v = (value or "").strip()
    if not v:
        return False
    if v in {"plugin", "openapi", "custom_gpt"}:
        return False
    return v == resolve_predefined_mcp_client_id()


def issuer_from_env() -> str | None:
    iss = (os.environ.get("KEYCLOAK_ISSUER") or "").strip() or settings.KEYCLOAK_ISSUER
    return iss.rstrip("/") if iss else None


def build_oauth_issuer_metadata() -> dict | None:
    """Minimal OAuth Authorization Server Metadata (RFC 8414) for agents that probe issuer."""
    iss = issuer_from_env()
    if not iss:
        return None
    base = f"{iss}/protocol/openid-connect"
    return {
        "issuer": iss,
        "authorization_endpoint": f"{base}/auth",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/clients-registrations/openid-connect",
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "response_types_supported": ["code"],
        "scopes_supported": list(MCP_CLIENT_SCOPES),
    }


def keycloak_realm_base_from_issuer() -> str | None:
    """Keycloak issuer `https://host/realms/{realm}` → base for well-known probing."""
    iss = issuer_from_env()
    if not iss:
        return None
    parts = urllib.parse.urlparse(iss)
    if "/realms/" not in parts.path:
        return iss
    return iss
