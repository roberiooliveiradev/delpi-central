"""Rotas de metadata OAuth Protected Resource da CLARA."""

from __future__ import annotations

from delpi_mcp.resource_contract import mcp_metadata_router as _build_router

from controllership_finance_app.interface.mcp.resource_metadata import (
    MCP_RESOURCE_CONFIG,
)

router = _build_router(
    MCP_RESOURCE_CONFIG, tags=["CLARA MCP OAuth Metadata"]
)
