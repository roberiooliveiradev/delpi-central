"""Conformance runner tests — including both VISTA incident regressions."""

from __future__ import annotations

from delpi_mcp.conformance import (
    ConformanceStatus,
    McpConformanceConfig,
    run_mcp_conformance,
)
from delpi_mcp.protocol import (
    DELPI_MCP_PROTOCOL_MINIMUM,
    check_protocol_minimum,
)


def _tool(name: str, meta: dict | None = None) -> dict:
    t = {
        "name": name,
        "description": "x",
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True},
    }
    if meta is not None:
        t["_meta"] = meta
    return t


def _config(**over) -> McpConformanceConfig:
    base = dict(
        name="test-mcp",
        expected_tool_names=("a", "b"),
        expected_tool_count=2,
        provider_profile="core",
        sdk_latest_protocol=DELPI_MCP_PROTOCOL_MINIMUM,
    )
    base.update(over)
    return McpConformanceConfig(**base)


def _tools() -> list[dict]:
    return [_tool("a"), _tool("b")]


def _result(report, gate):
    return next(r for r in report.results if r.gate == gate)


# --- happy path -------------------------------------------------------------


def test_fully_compliant_server_passes_all_gates():
    report = run_mcp_conformance(_tools(), _config())
    assert report.passed
    assert report.failures == []


def test_tool_count_mismatch_fails():
    report = run_mcp_conformance(_tools(), _config(expected_tool_count=5))
    assert _result(report, "expected_tool_count").status is ConformanceStatus.FAIL


def test_manifest_mismatch_fails_with_details():
    tools = [_tool("a"), _tool("zzz")]
    report = run_mcp_conformance(tools, _config())
    gate = _result(report, "expected_tool_manifest")
    assert gate.status is ConformanceStatus.FAIL
    assert gate.details["extra"] == ["zzz"]


# --- VISTA incident 1: reserved _meta.securitySchemes as strings ------------


def test_vista_string_security_schemes_incident_caught():
    tools = [
        _tool(
            "a",
            meta={"securitySchemes": ["openid", "profile", "email", "mcp:tools"]},
        ),
        _tool("b"),
    ]
    report = run_mcp_conformance(tools, _config())
    gate = _result(report, "security_schemes_shape")
    assert gate.status is ConformanceStatus.FAIL
    assert "reserved_meta" in {r.gate for r in report.results}
    assert _result(report, "reserved_meta").status is ConformanceStatus.FAIL


# --- VISTA incident 2: protocol-era capability ------------------------------


def test_protocol_minimum_v2_passes():
    check = check_protocol_minimum("2026-07-28")
    assert check.support == "SUPPORTED"


def test_protocol_minimum_below_floor_is_hard_fail():
    config = _config(sdk_latest_protocol="2025-11-25")
    report = run_mcp_conformance(_tools(), config)
    gate = _result(report, "protocol_minimum")
    assert gate.status is ConformanceStatus.FAIL
    assert gate in report.failures


def test_protocol_minimum_undeclared_is_inconclusive():
    config = _config(sdk_latest_protocol=None)
    report = run_mcp_conformance(_tools(), config)
    assert _result(report, "protocol_minimum").status is ConformanceStatus.INCONCLUSIVE


def test_protocol_unknown_version_is_unsupported():
    check = check_protocol_minimum("not-a-version")
    assert check.support == "UNSUPPORTED"
