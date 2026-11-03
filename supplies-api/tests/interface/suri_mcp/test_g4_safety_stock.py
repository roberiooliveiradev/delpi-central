"""SURI-MCP V7 G4 — safety_stock read dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (SafetyStockScopeFilters,
    SafetyStockItemsFilters, SafetyStockItemIdentity,
    SafetyStockSummaryFilters,
    PurchaseOrderSearchFilters,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    def has_permission(self, code): return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    ss = MagicMock()
    for m in ("get_filters", "get_summary", "list_items",
              "get_item_details", "get_item_suppliers"):
        getattr(ss, m).return_value = {"ok": True}
    with patch.object(tool_bridge, "_SAFETY_STOCK_SERVICE", ss), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield ss


def test_safety_filters_reaches_service(env):
    m = SafetyStockScopeFilters.model_validate({"branch": "01"})
    r = tool_bridge.tool_read("safety_stock", "filters", m)
    assert _ok(r), r
    env.get_filters.assert_called_once()


def test_safety_summary_and_items(env):
    m = SafetyStockSummaryFilters.model_validate({"branch": "01"})
    r = tool_bridge.tool_read("safety_stock", "summary", m)
    assert _ok(r), r
    kw = env.get_summary.call_args.kwargs
    assert kw["branch"] == "01" and "late_only" not in kw
    m2 = SafetyStockItemsFilters.model_validate(
        {"branch": "01", "page": 1, "page_size": 50})
    r = tool_bridge.tool_read("safety_stock", "items", m2)
    assert _ok(r), r
    kw = env.list_items.call_args.kwargs
    assert kw["branch"] == "01" and kw["page"] == 1


def test_safety_details_identity(env):
    ident = SafetyStockItemIdentity.model_validate(
        {"code": "M001", "branch": "01"})
    r = tool_bridge.tool_read("safety_stock", "details", None, ident)
    assert _ok(r), r
    env.get_item_details.assert_called_once()


def test_safety_suppliers_identity(env):
    ident = {"code": "M001", "branch": "01"}
    r = tool_bridge.tool_read("safety_stock", "suppliers", None, ident)
    assert _ok(r), r
    env.get_item_suppliers.assert_called_once()


def test_safety_details_rejects_filters(env):
    r = tool_bridge.tool_read(
        "safety_stock", "details", {"branch": "01"}, {"code": "X"})
    assert not _ok(r)


def test_safety_unknown_filter_rejected(env):
    r = tool_bridge.tool_read(
        "safety_stock", "items", {"branch": "01", "bogus": 1})
    assert not _ok(r)


def test_safety_unknown_action_rejected(env):
    r = tool_bridge.tool_read(
        "safety_stock", "export", {"branch": "01"})
    assert not _ok(r)
