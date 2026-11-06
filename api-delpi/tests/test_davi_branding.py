"""DAVI branding must not rename technical MCP/plugin identities."""

from __future__ import annotations

from app.interface.mcp.branding import (
    DAVI_FULL_NAME,
    DAVI_MCP_INSTRUCTIONS,
    DAVI_PLUGIN_DESCRIPTION,
    DAVI_SHORT_NAME,
)
from app.interface.mcp.oauth_contract import (
    CANONICAL_MCP_RESOURCE_URL,
    MCP_PREDEFINED_CLIENT_ID,
)
from app.interface.mcp.server import create_mcp_server