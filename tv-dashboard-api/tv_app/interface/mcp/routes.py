"""HTTP routes that complement the FastMCP mount (OAuth discovery only)."""

from __future__ import annotations

from delpi_mcp.resource_contract import mcp_metadata_router as _build_metadata_router

from .resource_metadata import MCP_RESOURCE_CONFIG

mcp_metadata_router = _build_metadata_router(MCP_RESOURCE_CONFIG)
