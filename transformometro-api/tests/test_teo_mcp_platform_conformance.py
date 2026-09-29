"""Platform conformance: run the shared delpi_mcp gate set over TÉO's real
serialized tools/list.

TÉO runs mcp 1.x (declared legacy migration state): the protocol_minimum
gate must report KNOWN_DRIFT, not PASS and not a silent skip.
"""

from __future__ import annotations

import asyncio

import pytest
from delpi_mcp.conformance import (
    CLASSIFICATION_KNOWN_DRIFT,
    McpConformanceConfig,
    run_mcp_conformance,
)
from delpi_mcp.protocol import DELPI_MCP_PROTOCOL_MINIMUM
from mcp.types import LATEST_PROTOCOL_VERSION

from tm_app.interface.mcp.constants import MCP_TOOL_NAMES
from tm_app.interface.mcp.server import create_mcp_server


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]


@pytest.fixture(scope="module")
def report():
    config = McpConformanceConfig(
        name="transformometro",
        expected_tool_names=tuple(MCP_TOOL_NAMES),
        expected_tool_count=len(MCP_TOOL_NAMES),
        provider_profile="openai",
        sdk_generation="v1",
        sdk_latest_protocol=LATEST_PROTOCOL_VERSION,
        protocol_minimum=DELPI_MCP_PROTOCOL_MINIMUM,
        legacy_protocol_allowed=True,
    )
    return run_mcp_conformance(_wire_tools(), config)


def test_no_hard_failures(report):
    assert report.hard_failures == [], report.summary()


def test_protocol_minimum_is_known_drift(report):
    """mcp 1.x cannot serve the 2026-07-28 era — reported, not hidden."""
    gate = next(r for r in report.results if r.gate == "protocol_minimum")
    assert gate.status.value == "FAIL"
    assert gate.classification == CLASSIFICATION_KNOWN_DRIFT


def test_tool_manifest_exact(report):
    gate = next(r for r in report.results if r.gate == "expected_tool_manifest")
    assert gate.status.value == "PASS"
