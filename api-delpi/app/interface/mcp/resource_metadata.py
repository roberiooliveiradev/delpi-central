"""OAuth Protected Resource Metadata for the API DELPI MCP endpoint (RFC 9728)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    resolve_required_mcp_resource_audience,
    resolve_resource_metadata_url,
)


def resolve_public_base_url() -> str | None:
    value = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    return value or None


def resolve_authorization_server_issuer() -> str | None:
    issuer = (os.getenv("KEYCLOAK_ISSUER") or "").strip().rstrip("/")
    return issuer or None


def resolve_mcp_resource_url() -> str:
    """Canonical MCP resource identifier — exact match, no trailing-slash rewrite."""
    return resolve_required_mcp_resource_audience()


def build_oauth_protected_resource_metadata() -> dict[str, Any]:
    """RFC 9728 document advertised to MCP clients (ChatGPT/Codex)."""
    resource = resolve_mcp_resource_url()
    issuer = resolve_authorization_server_issuer()
    auth_servers = [issuer] if issuer else []
    return {
        "resource": resource,
        "authorization_servers": auth_servers,
        "scopes_supported": list(MCP_OAUTH_SCOPES),
        "bearer_methods_supported": ["header"],
        "resource_documentation": (
            "https://github.com/roberiooliveiradev/delpi-central/blob/main/"
            "api-delpi/docs/integrations/openai-plugin-mcp.md"
        ),
    }


def www_authenticate_challenge(
    *,
    error: str | None = None,
    error_description: str | None = None,
) -> str:
    return build_www_authenticate_challenge(
        error=error,
        error_description=error_description,
    )


def public_host_allowed_for_mcp() -> tuple[list[str], list[str]]:
    """Hosts/origins for MCP DNS-rebinding protection derived from PUBLIC_BASE_URL."""
    hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    origins = [
        "http://127.0.0.1:*",
        "http://localhost:*",
        "http://[::1]:*",
    ]
    base = resolve_public_base_url()
    if not base:
        return hosts, origins
    parsed = urlparse(base)
    host = parsed.hostname
    if not host:
        return hosts, origins
    hosts.append(host)
    hosts.append(f"{host}:*")
    scheme = parsed.scheme or "https"
    if parsed.port:
        origins.append(f"{scheme}://{host}:{parsed.port}")
    else:
        origins.append(f"{scheme}://{host}")
    return hosts, origins


__all__ = [
    "build_oauth_protected_resource_metadata",
    "public_host_allowed_for_mcp",
    "resolve_authorization_server_issuer",
    "resolve_mcp_resource_url",
    "resolve_public_base_url",
    "resolve_resource_metadata_url",
    "www_authenticate_challenge",
]
