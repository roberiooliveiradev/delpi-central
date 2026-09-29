"""HTTP routes for MCP OAuth Protected Resource Metadata (public)."""

from __future__ import annotations

from delpi_mcp.resource_contract import mcp_metadata_router as _build_metadata_router

from app.interface.mcp.resource_metadata import MCP_RESOURCE_CONFIG

router = _build_metadata_router(
    MCP_RESOURCE_CONFIG, tags=["API DELPI MCP OAuth Metadata"]
)
