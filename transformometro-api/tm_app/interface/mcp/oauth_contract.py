"""OAuth/MCP contract for Transformômetro Plugin (TÉO).

Scopes in JWT ``scope`` claim only. Keycloak ``audience-delpi`` mints
``aud=delpi-central`` and must NOT be required as a scope string.

Resource audience = exact MCP URL (no trailing slash).
"""

from __future__ import annotations

import os
from typing import Any

from tm_app.interface.mcp.constants import (
    CANONICAL_MCP_RESOURCE_URL,
    MCP_GATEWAY_ROOT,
    MCP_PREDEFINED_CLIENT_ID,
)

MCP_OAUTH_SCOPES: tuple[str, ...] = (
    "openid",
    "profile",
    "email",
    "mcp:tools",
)

MCP_RESOURCE_BINDING_SCOPE = "mcp:tools"
KEYCLOAK_INTERNAL_AUDIENCE_CLIENT_SCOPE = "audience-delpi"

TEO_MCP_SECURITY_SCHEMES: list[dict[str, Any]] = [
    {
        "type": "oauth2",
        "scopes": list(MCP_OAUTH_SCOPES),
    }
]


def resolve_resource_metadata_url() -> str:
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    root = MCP_GATEWAY_ROOT.rstrip("/")
    if base:
        return f"{base}{root}/.well-known/oauth-protected-resource"
    return f"https://TO_CONFIGURE{root}/.well-known/oauth-protected-resource"


def resolve_required_mcp_resource_audience() -> str:
    """Exact MCP resource audience required in JWT ``aud``."""
    configured = (os.getenv("MCP_RESOURCE_URL") or "").strip()
    if configured:
        return configured
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}{MCP_GATEWAY_ROOT.rstrip('/')}/mcp"
    return CANONICAL_MCP_RESOURCE_URL


def build_www_authenticate_challenge(
    *,
    error: str | None = None,
    error_description: str | None = None,
) -> str:
    metadata_url = resolve_resource_metadata_url()
    parts = [
        "Bearer",
        'realm="transformometro-mcp"',
        f'resource_metadata="{metadata_url}"',
        f'scope="{" ".join(MCP_OAUTH_SCOPES)}"',
    ]
    if error:
        parts.append(f'error="{error}"')
    if error_description:
        safe = error_description.replace('"', "'")
        parts.append(f'error_description="{safe}"')
    return " ".join(parts)


def mcp_www_authenticate_meta(
    *,
    error: str,
    error_description: str,
) -> dict[str, list[str]]:
    return {
        "mcp/www_authenticate": [
            build_www_authenticate_challenge(
                error=error,
                error_description=error_description,
            )
        ]
    }


def extract_token_scopes(claims: dict[str, Any]) -> set[str]:
    raw = claims.get("scope") or claims.get("scp") or ""
    if isinstance(raw, (list, tuple, set)):
        return {str(item).strip() for item in raw if str(item).strip()}
    return {part for part in str(raw).split() if part}


def missing_required_oauth_scopes(claims: dict[str, Any]) -> list[str]:
    present = extract_token_scopes(claims)
    return [scope for scope in MCP_OAUTH_SCOPES if scope not in present]


def extract_token_audiences(claims: dict[str, Any]) -> set[str]:
    raw = claims.get("aud")
    if raw is None:
        return set()
    if isinstance(raw, str):
        value = raw.strip()
        return {value} if value else set()
    if isinstance(raw, (list, tuple, set)):
        return {str(item).strip() for item in raw if str(item).strip()}
    return set()


def token_has_exact_audience(claims: dict[str, Any], expected: str) -> bool:
    target = (expected or "").strip()
    if not target:
        return False
    return target in extract_token_audiences(claims)


__all__ = [
    "KEYCLOAK_INTERNAL_AUDIENCE_CLIENT_SCOPE",
    "MCP_OAUTH_SCOPES",
    "MCP_PREDEFINED_CLIENT_ID",
    "MCP_RESOURCE_BINDING_SCOPE",
    "TEO_MCP_SECURITY_SCHEMES",
    "build_www_authenticate_challenge",
    "extract_token_audiences",
    "extract_token_scopes",
    "mcp_www_authenticate_meta",
    "missing_required_oauth_scopes",
    "resolve_required_mcp_resource_audience",
    "resolve_resource_metadata_url",
    "token_has_exact_audience",
]
