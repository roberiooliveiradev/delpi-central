"""SURI-MCP V9 G6 — consumption-audit read dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    ConsumptionComparisonFilters, ConsumptionSearchFilters,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    def has_permission(self, code): return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    gw = MagicMock()
    gw.get.return_value = {"data": {"items": [], "total": 0}}
    with patch.object(tool_bridge, "_S2S_GATEWAY", gw), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield gw


def test_consumption_search_reaches_gateway(env):
    m = ConsumptionSearchFilters.model_validate({"unit": "01"})
    r = tool_bridge.tool_read("consumption", "search", m)
    assert _ok(r), r
    call = env.get.call_args
    assert call.args[0] == "/supplies/consumption-audit/orders"
    assert call.kwargs["params"]["branch"] == "01"


def test_consumption_search_rejects_bad_fragment(env):
    r = tool_bridge.tool_read(
        "consumption", "search", {"unit": "01", "search": "BAD!!"})
    assert not _ok(r)


def test_consumption_get_identity(env):
    ident = {"unit": "01", "production_order": "ABC12345678"}
    r = tool_bridge.tool_read("consumption", "get", None, ident)
    assert _ok(r), r
    call = env.get.call_args
    assert call.args[0] == "/supplies/consumption-audit/orders/ABC12345678"
    assert call.kwargs["params"]["branch"] == "01"


def test_consumption_get_rejects_short_key(env):
    r = tool_bridge.tool_read(
        "consumption", "get", None,
        {"unit": "01", "production_order": "SHORT"})
    assert not _ok(r)


def test_consumption_comparison_reaches_gateway(env):
    m = ConsumptionComparisonFilters.model_validate(
        {"unit": "01", "orders": ["ABC12345678", "DEF12345678"]})
    r = tool_bridge.tool_read("consumption", "comparison", m)
    assert _ok(r), r
    call = env.get.call_args
    assert call.args[0] == "/supplies/consumption-audit/comparison"
    assert call.kwargs["params"]["orders"] == "ABC12345678,DEF12345678"


def test_consumption_comparison_bounds(env):
    r = tool_bridge.tool_read(
        "consumption", "comparison",
        {"unit": "01", "orders": ["ABC12345678"]})
    assert not _ok(r)


def test_consumption_unit_required(env):
    r = tool_bridge.tool_read("consumption", "search", {})
    assert not _ok(r)


def test_consumption_unknown_action(env):
    r = tool_bridge.tool_read(
        "consumption", "export", {"unit": "01"})
    assert not _ok(r)
