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

SEARCH_PRODUCTS_SECURITY_SCHEMES: list[dict[str, Any]] = [
    {
        "type": "oauth2",
        "scopes": list(MCP_OAUTH_SCOPES),
    }
]

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
    metadata_url = resolve_resource_metadata_url()
    parts = [
        "Bearer",
        'realm="api-delpi-mcp"',
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
    """Tool-result `_meta` payload required by OpenAI for OAuth linking UX."""
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
    """Normalize JWT ``aud`` (string or array) to a set of exact audience strings."""
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
    """Semantic membership check — exact string match, no trailing-slash rewrite."""
    target = (expected or "").strip()
    if not target:
        return False
    return target in extract_token_audiences(claims)
