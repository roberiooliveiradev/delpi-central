"""OAuth Protected Resource Metadata for Transformômetro MCP (RFC 9728)."""

from __future__ import annotations

import os
from typing import Any

from delpi_mcp.resource_contract import (
    McpResourceConfig,
    build_protected_resource_metadata,
    mcp_allowed_hosts_and_origins,
)

from tm_app.interface.mcp.oauth_contract import (
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    resolve_required_mcp_resource_audience,
    resolve_resource_metadata_url,
)

MCP_RESOURCE_CONFIG = McpResourceConfig(
    resolve_resource_url=lambda: resolve_required_mcp_resource_audience(),
    resolve_authorization_server=lambda: resolve_authorization_server_issuer(),
    required_scopes=MCP_OAUTH_SCOPES,
    resource_documentation=(
        "https://github.com/roberiooliveiradev/delpi-central/blob/main/"
        "transformometro-api/docs/integrations/openai-plugin-mcp.md"
    ),
    metadata_paths=(
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
    ),
    metadata_operation_ids=(
        "tm_mcp_oauth_protected_resource_metadata",
        "tm_mcp_oauth_protected_resource_metadata_path",
    ),
)


def resolve_public_base_url() -> str | None:
    value = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    return value or None


def resolve_authorization_server_issuer() -> str | None:
    issuer = (os.getenv("KEYCLOAK_ISSUER") or "").strip().rstrip("/")
    return issuer or None


def resolve_mcp_resource_url() -> str:
    return resolve_required_mcp_resource_audience()


def build_oauth_protected_resource_metadata() -> dict[str, Any]:
    return build_protected_resource_metadata(MCP_RESOURCE_CONFIG)


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
    return mcp_allowed_hosts_and_origins(resolve_public_base_url())


__all__ = [
    "build_oauth_protected_resource_metadata",
    "public_host_allowed_for_mcp",
    "resolve_authorization_server_issuer",
    "resolve_mcp_resource_url",
    "resolve_public_base_url",
    "resolve_resource_metadata_url",
    "www_authenticate_challenge",
]
