"""OAuth Protected Resource metadata routes for the SURI MCP app."""

from __future__ import annotations

from delpi_mcp.resource_contract import mcp_metadata_router as _build_router

from app.interfaces.mcp.resource_metadata import MCP_RESOURCE_CONFIG

router = _build_router(MCP_RESOURCE_CONFIG, tags=["SURI MCP OAuth Metadata"])
