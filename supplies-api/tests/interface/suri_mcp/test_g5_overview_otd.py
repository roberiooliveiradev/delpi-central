"""SURI-MCP V8 G5 — otd + overview_summary dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    OtdAggregateFilters, OtdSeriesFilters, OverviewSummaryFilters,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    def has_permission(self, code): return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    ov = MagicMock(); ov.compose.return_value = {"ok": True}
    oa = MagicMock(); oa.compose.return_value = {"ok": True}
    os_ = MagicMock(); os_.compose.return_value = {"ok": True}
    with patch.object(tool_bridge, "_OVERVIEW_SERVICE", ov), \
         patch.object(tool_bridge, "_OTD_AGG_SERVICE", oa), \
         patch.object(tool_bridge, "_OTD_SERIES_SERVICE", os_), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield ov, oa, os_


def test_otd_aggregate_reaches_service(env):
    ov, oa, os_ = env
    m = OtdAggregateFilters.model_validate({"branch": "01"})
    r = tool_bridge.tool_read("otd", "aggregate", m)
    assert _ok(r), r
    oa.compose.assert_called_once()
    assert oa.compose.call_args.kwargs["branch"] == "01"


def test_otd_series_single_branch(env):
    ov, oa, os_ = env
    m = OtdSeriesFilters.model_validate(
        {"branch": ["01"], "granularity": "month"})
    r = tool_bridge.tool_read("otd", "series", m)
    assert _ok(r), r
    kw = os_.compose.call_args.kwargs
    assert kw["branch"] == "01" and kw["granularity"] == "month"


def test_overview_summary_reaches_service(env):
    ov, oa, os_ = env
    m = OverviewSummaryFilters.model_validate({"branch": ["01"]})
    r = tool_bridge.tool_analyze("overview_summary", m)
    assert _ok(r), r
    ov.compose.assert_called_once()
    assert ov.compose.call_args.kwargs["branches"] == ["01"]


def test_otd_unknown_action_rejected(env):
    r = tool_bridge.tool_read("otd", "export", {"branch": "01"})
    assert not _ok(r)


def test_otd_series_rejects_extra_key(env):
    r = tool_bridge.tool_read(
        "otd", "series", {"branch": ["01"], "bogus": 1})
    assert not _ok(r)


def test_overview_summary_rejects_extra_key(env):
    r = tool_bridge.tool_analyze(
        "overview_summary", {"branch": ["01"], "bogus": 1})
    assert not _ok(r)
