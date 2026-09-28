"""Frozen VISTA/TV MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. Do not rename for «VISTA».

Surface (MCP1): READ-only semantic tools. Write/mutation capabilities arrive
in MCP2 as PREPARE→proposal_handle→commit_proposal envelope tools over the
existing changes/preview|commit governed flow — never as per-op tools.
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP (not a shared client).
MCP_PREDEFINED_CLIENT_ID = "mcp-tv-dashboard"

# Public path convention proven in docker-compose (TV_DASHBOARD_API_ROOT_PATH)
# and by the TÉO resource URL (/apps/transformometro-api/mcp).
MCP_GATEWAY_ROOT = "/apps/tv-dashboard-api"

CANONICAL_MCP_RESOURCE_URL = "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# MCP1 surface: semantic READ tools only.
VISTA_MCP_SURFACE = "READ_V1"

# READ (MCP1). PREPARE/ACT classes reserved for MCP2 envelope tools.
TOOL_CLASS: dict[str, str] = {
    "list_playlists": "READ",
    "get_playlist_context": "READ",
    "get_catalog": "READ",
    "search_data_routes": "READ",
    "inspect_data_model": "READ",
    "preview_data_model": "READ",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# Names that must never appear in tools/list for this surface. MCP2 writes are
# envelope tools (prepare_change/commit_proposal), not per-op tools.
MCP_FORBIDDEN_TOOLS: frozenset[str] = frozenset(
    {
        "prepare_change",
        "commit_proposal",
        "upsert_data_model",
        "delete_data_model",
        "bind_visual",
        "migrate_data_sources_to_model",
        "upsert_data_source",
        "set_data_transform",
        "patch_data_source_params",
        "preview_data_block",
        "suggest_change",
        "execute_capability",
        "invoke_tool",
        "generic_http",
        "sql",
    }
)
