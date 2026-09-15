"""OAuth/MCP contract constants and challenge builders (OpenAI Plugin auth).

OAuth scopes are identity/token issuance scopes proven in Keycloak discovery.
They are NOT RBAC permission codes and must never expose ENGINEERING_LMP_ACCESS.
"""

from __future__ import annotations

import os
from typing import Any

# Proven on live Keycloak OIDC discovery (realm delpi) + platform audience mapper docs.
# Minimal set for user identity + delpi-central audience issuance.
MCP_OAUTH_SCOPES: tuple[str, ...] = (
    "openid",
    "profile",
    "email",
    "audience-delpi",
)

SEARCH_PRODUCTS_SECURITY_SCHEMES: list[dict[str, Any]] = [
    {
        "type": "oauth2",
        "scopes": list(MCP_OAUTH_SCOPES),
    }
]

# Auth model: entire MCP Streamable HTTP transport requires OAuth before tools/list.
MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"


def resolve_resource_metadata_url() -> str:
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/apps/api-delpi/.well-known/oauth-protected-resource"
    return "https://TO_CONFIGURE/apps/api-delpi/.well-known/oauth-protected-resource"


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
