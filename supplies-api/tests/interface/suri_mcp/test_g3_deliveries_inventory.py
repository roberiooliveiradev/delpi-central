"""SURI-MCP-V6-G3 — deliveries.late + inventory.summary/items dispatch."""
from unittest.mock import MagicMock, patch
import pytest
from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    InventoryItemsFilters, InventorySummaryFilters, PurchaseOrderSearchFilters,
)


class _User:
    is_superadmin = True
    access_token = "tok"
    def has_permission(self, code): return True


def _ok(r):
    return getattr(r, "is_error", getattr(r, "isError", False)) is False


@pytest.fixture
def env():
    d = MagicMock(); d.compose.return_value = {"items": [], "total": 0}
    i = MagicMock()
    i.get_summary.return_value = {"items": []}
    i.list_items.return_value = {"items": [], "total": 0}
    with patch.object(tool_bridge, "_DELIVERIES_SERVICE", d), \
         patch.object(tool_bridge, "_INVENTORY_SERVICE", i), \
         patch.object(tool_bridge, "_effective_user", return_value=_User()):
        yield d, i


def test_deliveries_late_reaches_compose(env):
    d, i = env
    model = PurchaseOrderSearchFilters.model_validate({"branch": ["01"]})
    r = tool_bridge.tool_read("deliveries", "late", model)
    assert _ok(r), r
    d.compose.assert_called_once()
    kw = d.compose.call_args.kwargs
    assert kw["branches"] == ["01"]
    assert "late_only" not in kw


def test_inventory_summary_reaches_service(env):
    d, i = env
    model = InventorySummaryFilters.model_validate({"branch": ["01"]})
    r = tool_bridge.tool_read("inventory", "summary", model)
    assert _ok(r), r
    i.get_summary.assert_called_once()


def test_inventory_items_reaches_service(env):
    d, i = env
    model = InventoryItemsFilters.model_validate(
        {"branch": ["01"], "page": 1, "page_size": 50, "sort": "quantity_desc"})
    r = tool_bridge.tool_read("inventory", "items", model)
    assert _ok(r), r
    kw = i.list_items.call_args.kwargs
    assert kw["sort"] == "quantity_desc" and kw["page"] == 1


def test_deliveries_rejects_unknown_filter(env):
    d, i = env
    r = tool_bridge.tool_read("deliveries", "late", {"branch": ["01"], "bogus": 1})
    assert not _ok(r)


def test_inventory_summary_rejects_items_filter(env):
    r = tool_bridge.tool_read("inventory", "summary", {"branch": ["01"], "sort": "x"})
    assert not _ok(r)


def test_unknown_action_rejected(env):
    r = tool_bridge.tool_read("inventory", "export", {"branch": ["01"]})
    assert not _ok(r)
