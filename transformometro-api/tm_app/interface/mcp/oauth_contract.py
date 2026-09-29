"""OAuth/MCP contract for Transformômetro Plugin (TÉO).

Scopes in JWT ``scope`` claim only. Keycloak ``audience-delpi`` mints
``aud=delpi-central`` and must NOT be required as a scope string.

Resource audience = exact MCP URL (no trailing slash).
"""

from __future__ import annotations

import os
from typing import Any

from delpi_mcp.resource_contract import (
    build_www_authenticate_challenge as _shared_build_challenge,
)
from delpi_mcp.resource_contract import (
    build_www_authenticate_meta as _shared_www_authenticate_meta,
)
from delpi_mcp.resource_contract import (
    extract_token_audiences as _shared_extract_token_audiences,
)
from delpi_mcp.resource_contract import (
    extract_token_scopes as _shared_extract_token_scopes,
)
from delpi_mcp.resource_contract import (
    missing_required_scopes as _shared_missing_required_scopes,
)
from delpi_mcp.resource_contract import (
    token_has_required_audience as _shared_token_has_audience,
)

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
    return _shared_build_challenge(
        realm="transformometro-mcp",
        metadata_url=resolve_resource_metadata_url(),
        scope_value=" ".join(MCP_OAUTH_SCOPES),
        error=error,
        error_description=error_description,
    )


def mcp_www_authenticate_meta(
    *,
    error: str,
    error_description: str,
) -> dict[str, list[str]]:
    return _shared_www_authenticate_meta(
        build_www_authenticate_challenge(
            error=error,
            error_description=error_description,
        ),
        wrap_in_list=True,
    )


def extract_token_scopes(claims: dict[str, Any]) -> set[str]:
    return _shared_extract_token_scopes(claims)


def missing_required_oauth_scopes(claims: dict[str, Any]) -> list[str]:
    return _shared_missing_required_scopes(claims, MCP_OAUTH_SCOPES)


def extract_token_audiences(claims: dict[str, Any]) -> set[str]:
    return _shared_extract_token_audiences(claims)


def token_has_exact_audience(claims: dict[str, Any], expected: str) -> bool:
    return _shared_token_has_audience(claims, expected)


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
