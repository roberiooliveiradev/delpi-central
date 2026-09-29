"""Platform conformance: shared delpi_mcp gate set over DAVI's real
serialized tools/list (mcp 2.x generation — expected fully green)."""

from __future__ import annotations

import asyncio

import pytest
from delpi_mcp.conformance import (
    McpConformanceConfig,
    run_mcp_conformance,
)
from delpi_mcp.protocol import DELPI_MCP_PROTOCOL_MINIMUM
from mcp.types import LATEST_PROTOCOL_VERSION

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
)
from app.interface.mcp.server import create_mcp_server

_DAVI_TOOLS = (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
)


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]


@pytest.fixture(scope="module")
def report():
    config = McpConformanceConfig(
        name="api-delpi",
        expected_tool_names=_DAVI_TOOLS,
        expected_tool_count=len(_DAVI_TOOLS),
        provider_profile="openai",
        sdk_generation="v2",
        sdk_latest_protocol=LATEST_PROTOCOL_VERSION,
        protocol_minimum=DELPI_MCP_PROTOCOL_MINIMUM,
        legacy_protocol_allowed=False,
    )
    return run_mcp_conformance(_wire_tools(), config)


def test_no_hard_failures(report):
    assert report.hard_failures == [], report.summary()


def test_protocol_minimum_satisfied(report):
    """mcp 2.x serves the 2026-07-28 era — S6 convergence gate."""
    gate = next(r for r in report.results if r.gate == "protocol_minimum")
    assert gate.status.value == "PASS"


def test_tool_manifest_exact(report):
    gate = next(r for r in report.results if r.gate == "expected_tool_manifest")
    assert gate.status.value == "PASS"
