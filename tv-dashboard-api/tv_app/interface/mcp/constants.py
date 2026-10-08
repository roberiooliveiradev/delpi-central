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

# MCP2 surface: semantic READ tools + governed PREPARE/ACT envelope.
VISTA_MCP_SURFACE = "GOVERNED_WRITE_V1"

# READ (MCP1) + governed envelope (MCP2). Native ops remain vocabulary inside
# prepare_change.ops[] — never per-op tools.
TOOL_CLASS: dict[str, str] = {
    "list_playlists": "READ",
    "get_playlist_context": "READ",
    "get_catalog": "DISCOVERY",
    "search_data_routes": "READ",
    "inspect_data_model": "READ",
    "preview_data_model": "READ",
    "preview_data_block": "ANALYSIS",
    "get_product_guide": "READ",
    "suggest_change": "ANALYSIS",
    "prepare_change": "PREPARE",
    "commit_proposal": "ACT",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# Names that must never appear in tools/list for this surface. Writes flow
# exclusively through prepare_change/commit_proposal envelope tools.
MCP_FORBIDDEN_TOOLS: frozenset[str] = frozenset(
    {
        "upsert_data_model",
        "patch_data_model",
        "delete_data_model",
        "bind_visual",
        "migrate_data_sources_to_model",
        "upsert_data_source",
        "set_data_transform",
        "patch_data_source_params",
        "preview_change",
        "commit_change",
        "execute_capability",
        "invoke_tool",
        "generic_http",
        "sql",
    }
)
