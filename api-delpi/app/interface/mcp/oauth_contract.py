"""OAuth/MCP contract constants and challenge builders (OpenAI Plugin auth).

OAuth scopes advertised/required on the MCP resource server are ONLY those
expected in the JWT ``scope`` claim.

Distinction (proven with Keycloak 26.0.7 + client ``mcp-api-delpi``):

- identity scopes (in JWT scope): ``openid``, ``profile``, ``email``
- MCP resource-binding scope (in JWT scope): ``mcp:tools``
- Keycloak internal audience client scope: ``audience-delpi``
  → causes ``aud`` to include ``delpi-central``
  → does NOT appear in JWT ``scope`` and MUST NOT be required there
- business authorization: ``ENGINEERING_LMP_ACCESS`` (RBAC, never an OAuth scope)

Keycloak 26.x does not natively process RFC 8707 ``resource`` → aud.
Official workaround: client scope ``mcp:tools`` with Audience mapper whose
Included Custom Audience equals the MCP resource URL exactly.
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

# Required in JWT ``scope`` for MCP transport acceptance.
MCP_OAUTH_SCOPES: tuple[str, ...] = (
    "openid",
    "profile",
    "email",
    "mcp:tools",
)

MCP_RESOURCE_BINDING_SCOPE = "mcp:tools"

# Assigned on Keycloak client mcp-api-delpi (Default). Not a JWT scope claim.
KEYCLOAK_INTERNAL_AUDIENCE_CLIENT_SCOPE = "audience-delpi"

# OAuth securitySchemes advertised on every productive DAVI MCP tool.
# Historical alias SEARCH_PRODUCTS_SECURITY_SCHEMES kept for import compatibility.
DAVI_MCP_SECURITY_SCHEMES: list[dict[str, Any]] = [
    {
        "type": "oauth2",
        "scopes": list(MCP_OAUTH_SCOPES),
    }
]
SEARCH_PRODUCTS_SECURITY_SCHEMES = DAVI_MCP_SECURITY_SCHEMES

# Auth model: entire MCP Streamable HTTP transport requires OAuth before tools/list.
MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# Predefined Keycloak client for OpenAI Plugin / MCP (do not reuse Portal / GPT bridge clients).
MCP_PREDEFINED_CLIENT_ID = "mcp-api-delpi"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/api-delpi/mcp"


def resolve_resource_metadata_url() -> str:
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/apps/api-delpi/.well-known/oauth-protected-resource"
    return "https://TO_CONFIGURE/apps/api-delpi/.well-known/oauth-protected-resource"


def resolve_required_mcp_resource_audience() -> str:
    """Exact MCP resource audience required in JWT ``aud`` (no slash normalization)."""
    configured = (os.getenv("MCP_RESOURCE_URL") or "").strip()
    if configured:
        return configured
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/apps/api-delpi/mcp"
    return CANONICAL_MCP_RESOURCE_URL


def build_www_authenticate_challenge(
    *,
    error: str | None = None,
    error_description: str | None = None,
) -> str:
    """RFC 9728 / OpenAI Bearer challenge (no internal details)."""
    return _shared_build_challenge(
        realm="api-delpi-mcp",
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
    """Tool-result `_meta` payload required by OpenAI for OAuth linking UX."""
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
    """Normalize JWT ``aud`` (string or array) to a set of exact audience strings."""
    return _shared_extract_token_audiences(claims)


def token_has_exact_audience(claims: dict[str, Any], expected: str) -> bool:
    """Semantic membership check — exact string match, no trailing-slash rewrite."""
    return _shared_token_has_audience(claims, expected)
