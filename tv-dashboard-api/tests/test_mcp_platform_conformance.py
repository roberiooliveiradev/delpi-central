"""Platform conformance: run the shared delpi_mcp gate set over VISTA's
real serialized tools/list (mcp 2.x generation — expected fully green)."""

from __future__ import annotations

import asyncio

import pytest
from delpi_mcp.conformance import McpConformanceConfig, run_mcp_conformance
from delpi_mcp.protocol import DELPI_MCP_PROTOCOL_MINIMUM
from mcp.types import LATEST_PROTOCOL_VERSION

from tv_app.interface.mcp.constants import MCP_TOOL_NAMES
from tv_app.interface.mcp.server import create_mcp_server


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]


@pytest.fixture(scope="module")
def report():
    config = McpConformanceConfig(
        name="tv-dashboard",
        expected_tool_names=tuple(MCP_TOOL_NAMES),
        expected_tool_count=len(MCP_TOOL_NAMES),
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
    gate = next(r for r in report.results if r.gate == "protocol_minimum")
    assert gate.status.value == "PASS"


def test_reserved_meta_clean(report):
    gate = next(r for r in report.results if r.gate == "reserved_meta")
    assert gate.status.value == "PASS", gate.message


def test_tool_manifest_exact(report):
    gate = next(r for r in report.results if r.gate == "expected_tool_manifest")
    assert gate.status.value == "PASS"
