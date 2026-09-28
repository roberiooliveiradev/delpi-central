"""RFC 9728 OAuth Protected Resource Metadata for the TV/VISTA MCP resource."""

from __future__ import annotations

import os
import urllib.parse

from tv_app.config import settings

from .oauth_contract import (
    MCP_CLIENT_SCOPES,
    issuer_from_env,
    resolve_required_mcp_resource_audience,
)

_PUBLIC_HOST_SUFFIXES = (".minhadelpi.com.br",)
_PUBLIC_HOSTS = frozenset({"minhadelpi.com.br", "localhost", "127.0.0.1"})


def protected_resource_metadata_url(resource_url: str | None = None) -> str:
    """Absolute URL of the metadata document (hosted on this API)."""
    resource = (resource_url or resolve_required_mcp_resource_audience()).rstrip("/")
    parsed = urllib.parse.urlparse(resource)
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path
    if path.endswith("/mcp"):
        path = path[: -len("/mcp")]
    return f"{base}{path}/.well-known/oauth-protected-resource"


def build_protected_resource_document(
    request_base_url: str,
    *,
    resource_url: str | None = None,
) -> dict:
    """Body for `GET /.well-known/oauth-protected-resource` (and optional prefixed alias)."""
    del request_base_url  # public canonical origin only — never derive from request host
    resource = (resource_url or resolve_required_mcp_resource_audience()).rstrip("/")
    issuer = issuer_from_env()
    authorization_servers: list[str] = [issuer] if issuer else []
    doc: dict = {
        "resource": resource,
        "authorization_servers": authorization_servers,
        "scopes_supported": list(MCP_CLIENT_SCOPES),
        "bearer_methods_supported": ["header"],
        "resource_signing_alg_values_supported": ["RS256"],
        "resource_documentation": (
            "https://github.com/delpi/delpi-central/blob/main/"
            "tv-dashboard-api/docs/integrations/openai-plugin-mcp.md"
        ),
    }
    return doc


def public_host_allowed_for_mcp(host: str | None) -> bool:
    """Restrict MCP surface to public hostname (not internal docker names)."""
    if not host:
        return False
    h = host.split(":")[0].lower().strip()
    if h in _PUBLIC_HOSTS:
        return True
    return any(h.endswith(sfx) for sfx in _PUBLIC_HOST_SUFFIXES)


def www_authenticate_challenge() -> str:
    from .oauth_contract import build_www_authenticate_challenge

    return build_www_authenticate_challenge(include_mcp_tools_scope=True)
