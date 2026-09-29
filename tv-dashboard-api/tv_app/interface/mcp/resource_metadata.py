"""RFC 9728 OAuth Protected Resource Metadata for the TV/VISTA MCP resource."""

from __future__ import annotations

from delpi_mcp.resource_contract import (
    McpResourceConfig,
    build_protected_resource_metadata,
)
from delpi_mcp.resource_contract import (
    protected_resource_metadata_url as _shared_metadata_url,
)

from .oauth_contract import (
    MCP_CLIENT_SCOPES,
    issuer_from_env,
    resolve_required_mcp_resource_audience,
)

_PUBLIC_HOST_SUFFIXES = (".minhadelpi.com.br",)
_PUBLIC_HOSTS = frozenset({"minhadelpi.com.br", "localhost", "127.0.0.1"})

MCP_RESOURCE_CONFIG = McpResourceConfig(
    resolve_resource_url=resolve_required_mcp_resource_audience,
    resolve_authorization_server=issuer_from_env,
    required_scopes=MCP_CLIENT_SCOPES,
    resource_documentation=(
        "https://github.com/delpi/delpi-central/blob/main/"
        "tv-dashboard-api/docs/integrations/openai-plugin-mcp.md"
    ),
    resource_signing_alg_values_supported=("RS256",),
    metadata_paths=(
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/apps/tv-dashboard-api/mcp",
    ),
)


def protected_resource_metadata_url(resource_url: str | None = None) -> str:
    """Absolute URL of the metadata document (hosted on this API)."""
    resource = resource_url or resolve_required_mcp_resource_audience()
    return _shared_metadata_url(resource)


def build_protected_resource_document(
    request_base_url: str,
    *,
    resource_url: str | None = None,
) -> dict:
    """Body for `GET /.well-known/oauth-protected-resource` (and optional prefixed alias)."""
    del request_base_url  # public canonical origin only — never derive from request host
    return build_protected_resource_metadata(MCP_RESOURCE_CONFIG, resource_url=resource_url)


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
