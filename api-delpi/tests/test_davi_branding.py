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


def test_davi_branding_constants() -> None:
    assert DAVI_SHORT_NAME == "DAVI"
    assert DAVI_FULL_NAME.startswith("DAVI")
    assert "DELPI" in DAVI_FULL_NAME
    assert "DAVI" in DAVI_PLUGIN_DESCRIPTION
    assert "DAVI" in DAVI_MCP_INSTRUCTIONS
    assert "search_products" in DAVI_MCP_INSTRUCTIONS
    assert "discover_delpi_information" in DAVI_MCP_INSTRUCTIONS
    assert "agent_directives" in DAVI_MCP_INSTRUCTIONS


def test_technical_ids_unchanged_by_davi_branding() -> None:
    assert MCP_PREDEFINED_CLIENT_ID == "mcp-api-delpi"
    assert CANONICAL_MCP_RESOURCE_URL == "https://minhadelpi.com.br/apps/api-delpi/mcp"
    mcp = create_mcp_server()
    assert mcp.name == "api-delpi"
    assert "DAVI" in (mcp.instructions or "")
    tools = mcp._tool_manager.list_tools()
    assert [t.name for t in tools] == [
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    ]
