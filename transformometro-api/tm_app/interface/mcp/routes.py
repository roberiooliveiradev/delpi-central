"""HTTP routes for Transformômetro MCP OAuth Protected Resource Metadata."""

from __future__ import annotations

from delpi_mcp.resource_contract import mcp_metadata_router as _build_metadata_router

from tm_app.interface.mcp.resource_metadata import MCP_RESOURCE_CONFIG

router = _build_metadata_router(
    MCP_RESOURCE_CONFIG, tags=["Transformômetro MCP OAuth Metadata"]
)
