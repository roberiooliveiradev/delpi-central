"""SURI-MCP V10 G7 — market + comex read dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    MarketSeriesFilters, MarketQuoteFilters, MarketCommonFilters,
    ComexProductsFilters, ComexNcmListFilters,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "u1"

    def has_permission(self, code):
        return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    mkt = MagicMock()
    for m in ("get_filters", "get_summary", "list_series",
              "list_import_series", "list_producer_price_series",
              "list_fx_series", "list_quotes_series",
              "list_quotes_compare", "list_monthly_averages"):
        getattr(mkt, m).return_value = {"ok": True}
    cmx = MagicMock()
    cmx.search_products.return_value = {"items": []}
    cmx.list_governance.return_value = []
    cmx.get_governance.return_value = {"id": "g1"}
    cmx.list_views.return_value = []
    cmx.get_view.return_value = {"id": "v1"}
    with patch.object(tool_bridge, "_MARKET_SERVICE", mkt), \
         patch.object(tool_bridge, "_COMEX_SERVICE", cmx), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield mkt, cmx


def test_market_filters(env):
    r = tool_bridge.tool_read("market", "filters", {})
    assert _ok(r), r
    mkt, _ = env
    mkt.get_filters.assert_called_once()


def test_market_series_kwargs(env):
    mkt, _ = env
    m = MarketSeriesFilters.model_validate(
        {"instrument": "BBAS3", "granularity": "month"})
    r = tool_bridge.tool_read("market", "series", m)
    assert _ok(r), r
    kw = mkt.list_series.call_args.kwargs
    assert kw["instrument_code"] == "BBAS3" and kw["granularity"] == "month"


def test_market_quote_series(env):
    mkt, _ = env
    m = MarketQuoteFilters.model_validate({"instruments": "BBAS3,VALE3"})
    r = tool_bridge.tool_read("market", "quote_series", m)
    assert _ok(r), r
    assert mkt.list_quotes_series.call_args.kwargs["instruments"] == "BBAS3,VALE3"


def test_market_unknown_action(env):
    r = tool_bridge.tool_read("market", "export", {})
    assert not _ok(r)


def test_market_series_rejects_extra_key(env):
    r = tool_bridge.tool_read(
        "market", "series", {"instrument": "X", "bogus": 1})
    assert not _ok(r)


def test_comex_products(env):
    _, cmx = env
    m = ComexProductsFilters.model_validate({"code": "1234"})
    r = tool_bridge.tool_read("comex", "products_search", m)
    assert _ok(r), r
    cmx.search_products.assert_called_once()


def test_comex_ncm_list(env):
    _, cmx = env
    m = ComexNcmListFilters.model_validate({"status": "pending"})
    r = tool_bridge.tool_read("comex", "ncm_governance", m)
    assert _ok(r), r
    cmx.list_governance.assert_called_once()


def test_comex_governance_get(env):
    _, cmx = env
    r = tool_bridge.tool_read(
        "comex", "ncm_governance_get", None,
        {"governance_id": "abc-123"})
    assert _ok(r), r
    cmx.get_governance.assert_called_once()


def test_comex_views(env):
    _, cmx = env
    r = tool_bridge.tool_read("comex", "views", {})
    assert _ok(r), r
    cmx.list_views.assert_called_once()


def test_comex_view_get(env):
    _, cmx = env
    r = tool_bridge.tool_read(
        "comex", "view_get", None, {"view_id": "v-1"})
    assert _ok(r), r
    cmx.get_view.assert_called_once()


def test_comex_get_rejects_filters(env):
    r = tool_bridge.tool_read(
        "comex", "ncm_governance_get", {"status": "x"},
        {"governance_id": "abc"})
    assert not _ok(r)


def test_comex_unknown_action(env):
    r = tool_bridge.tool_read("comex", "export", {})
    assert not _ok(r)
