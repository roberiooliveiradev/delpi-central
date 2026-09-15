"""OAuth Protected Resource Metadata for the API DELPI MCP endpoint (RFC 9728)."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse


def resolve_public_base_url() -> str | None:
    value = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    return value or None


def resolve_authorization_server_issuer() -> str | None:
    issuer = (os.getenv("KEYCLOAK_ISSUER") or "").strip().rstrip("/")
    return issuer or None


def resolve_mcp_resource_url() -> str:
    """Canonical MCP resource identifier (stable path; host from PUBLIC_BASE_URL)."""
    configured = (os.getenv("MCP_RESOURCE_URL") or "").strip().rstrip("/")
    if configured:
        return configured
    base = resolve_public_base_url()
    if base:
        return f"{base}/apps/api-delpi/mcp"
    # Fail closed for metadata: placeholder host must not be treated as production-ready.
    return "https://TO_CONFIGURE/apps/api-delpi/mcp"


def resolve_resource_metadata_url() -> str:
    base = resolve_public_base_url()
    if base:
        return f"{base}/apps/api-delpi/.well-known/oauth-protected-resource"
    return "https://TO_CONFIGURE/apps/api-delpi/.well-known/oauth-protected-resource"


def build_oauth_protected_resource_metadata() -> dict[str, Any]:
    """RFC 9728 document advertised to MCP clients (ChatGPT/Codex)."""
    resource = resolve_mcp_resource_url()
    issuer = resolve_authorization_server_issuer()
    auth_servers = [issuer] if issuer else []
    scopes = [
        s.strip()
        for s in (os.getenv("MCP_OAUTH_SCOPES") or "openid profile email").split()
        if s.strip()
    ]
    doc: dict[str, Any] = {
        "resource": resource,
        "authorization_servers": auth_servers,
        "scopes_supported": scopes,
        "bearer_methods_supported": ["header"],
        "resource_documentation": (
            "https://github.com/roberiooliveiradev/delpi-central/blob/main/"
            "api-delpi/docs/integrations/openai-plugin-mcp.md"
        ),
    }
    return doc


def www_authenticate_challenge() -> str:
    metadata_url = resolve_resource_metadata_url()
    scopes = (os.getenv("MCP_OAUTH_SCOPES") or "openid profile email").strip()
    return (
        f'Bearer realm="api-delpi-mcp", '
        f'resource_metadata="{metadata_url}", '
        f'scope="{scopes}"'
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
