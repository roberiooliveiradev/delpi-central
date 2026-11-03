"""SURI V4 — procurement_diagnostic composition + contract."""
import json
import pytest
from unittest.mock import MagicMock, patch
from app.interfaces.mcp import tool_bridge
from app.application.services.procurement_diagnostic_service import (
    ProcurementDiagnosticService,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "a1"

    def has_permission(self, code):
        return True


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(tool_bridge, "_effective_user",
                        lambda: _User())


def _err(r):
    return getattr(r, "is_error", getattr(r, "isError", False))


def _data(r):
    d = json.loads(r.content[0].text)
    return d.get("data", d)


def _svc(**over):
    svc = ProcurementDiagnosticService()
    for k, v in over.items():
        setattr(svc, k, v)
    return svc


def _ok_payload(*_a, **_k):
    return {"summary": {"total": 7}}


def test_diagnostic_all_sections_ok():
    diag = _svc(
        _overview=MagicMock(compose=MagicMock(return_value={"kpi": 1})),
        _otd=MagicMock(compose=MagicMock(return_value={"otd": 90.1})),
        _deliveries=MagicMock(compose=MagicMock(return_value={"items": []})),
        _safety=MagicMock(
            get_summary=MagicMock(return_value={"summary": {"deficit_items": 3}})),
    )
    with patch.object(tool_bridge, "_PROC_DIAG_SERVICE", diag):
        r = tool_bridge.tool_analyze("procurement_diagnostic",
                                     {"branch": "01"})
    d = _data(r)
    assert _err(r) is False
    assert d["completeness"]["sections_data_gap"] == []
    names = {s["section"] for s in d["sections"]}
    assert {"overview", "otd", "deliveries", "safety_stock",
            "supply_risk"} <= names


def test_diagnostic_section_failure_isolated():
    diag = _svc(
        _overview=MagicMock(compose=MagicMock(
            side_effect=RuntimeError("boom"))),
        _otd=MagicMock(compose=MagicMock(return_value={"otd": 90.1})),
        _deliveries=MagicMock(compose=MagicMock(return_value={"items": []})),
        _safety=MagicMock(
            get_summary=MagicMock(return_value={"summary": {}})),
    )
    with patch.object(tool_bridge, "_PROC_DIAG_SERVICE", diag):
        r = tool_bridge.tool_analyze("procurement_diagnostic", {})
    d = _data(r)
    assert "overview" in d["completeness"]["sections_data_gap"]
    assert "otd" in d["completeness"]["sections_ok"]


def test_diagnostic_unknown_section_rejected():
    r = tool_bridge.tool_analyze(
        "procurement_diagnostic",
        {"include_sections": ["bogus"]})
    assert _err(r) is True


def test_diagnostic_unknown_filter_rejected():
    r = tool_bridge.tool_analyze(
        "procurement_diagnostic", {"bogus": 1})
    assert _err(r) is True


def test_diagnostic_unknown_analysis_rejected():
    r = tool_bridge.tool_analyze("fake_analysis", {})
    assert _err(r) is True


def test_supply_risk_no_invented_signal():
    diag = _svc(
        _safety=MagicMock(get_summary=MagicMock(
            return_value={"summary": {"deficit_items": 5}})),
    )
    with patch.object(tool_bridge, "_PROC_DIAG_SERVICE", diag):
        r = tool_bridge.tool_analyze(
            "procurement_diagnostic",
            {"include_sections": ["safety_stock", "supply_risk"]})
    d = _data(r)
    risk = next(s for s in d["sections"]
                if s["section"] == "supply_risk")
    assert risk["facts"]["signals"]
