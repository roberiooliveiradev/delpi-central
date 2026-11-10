"""DAVI MCP metadata must not contradict the live tool surface."""

from __future__ import annotations

from app.application.external_capabilities.constants import (
    MCP_TOOL_ANALYZE,
    MCP_TOOL_GET_CONTEXT,
    MCP_TOOL_KNOWLEDGE,
    MCP_TOOL_READ,
)
from app.application.external_capabilities.davi_agent_intelligence_service import (
    DaviAgentIntelligenceService,
)
from app.interface.mcp.server import create_mcp_server


def test_get_context_description_does_not_claim_read_unimplemented() -> None:
    server = create_mcp_server()
    tools = {
        tool.name: tool
        for tool in server._tool_manager.list_tools()
    }
    assert MCP_TOOL_GET_CONTEXT in tools
    assert MCP_TOOL_READ in tools
    assert MCP_TOOL_ANALYZE in tools
    assert MCP_TOOL_KNOWLEDGE in tools
    description = tools[MCP_TOOL_GET_CONTEXT].description or ""
    lowered = description.casefold()
    assert "read/analyze/execute/delete" not in lowered
    assert "not implemented" not in lowered or "execute/delete" in lowered
    assert "read or analyze" in lowered or "read/analyze" in lowered


def test_surface_parity_marks_read_analyze_live() -> None:
    note = DaviAgentIntelligenceService.agent_directives()["surface_parity"][
        "note"
    ]
    assert "read + analyze are LIVE" in note or "are LIVE" in note
    assert "read/analyze/execute/delete remain PLANNED_NOT_IMPLEMENTED" not in note
