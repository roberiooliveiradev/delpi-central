"""SURI-MCP-V5-G2-RESIDUAL-CLOSURE-001 (R4) — regression for the
production bug found by SURI-MCP-V4-G2-DEPLOY-001.

The `read` tool's `filters` argument is an 11-member pydantic union
declared in `server.py`. For a minimal payload such as
``{"branch": ["01"]}`` the union resolves to a *sibling* model
(`PurchaseOrderSearchFilters` — first member). Before the fix,
`_payload_dict` dumped that model with `exclude_none=True` only, so
defaults (`late_only`, `page`, `page_size`) leaked into the dispatch
dict as phantom keys and the closed-vocabulary dispatcher rejected
*every* `purchase_requests` action and `purchase_orders export` at
runtime — a path unit tests never exercised (they pass dicts to
handlers).

These tests exercise the real path: union-resolved sibling model ->
`_payload_dict` -> `tool_read` dispatch -> handler (gateway mocked).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.interfaces.mcp import tool_bridge
from app.interfaces.mcp.schemas import (
    PurchaseOrderExportFilters,
    PurchaseOrderSearchFilters,
    PurchaseRequestExportFilters,
    PurchaseRequestIdentity,
    PurchaseRequestSearchFilters,
)


class _User:
    is_superadmin = True
    permissions = {"supplies.access"}
    access_token = "tok"

    def has_permission(self, code):  # noqa: D401 - test stub
        return True


def _pr_ok(items=None):
    return {"data": {"items": items or [], "total": len(items or [])}}


@pytest.fixture
def pr_gateway():
    gw = MagicMock()
    gw.list_purchase_requests.return_value = _pr_ok(
        [{"branch": "01", "request_number": "179309"}]
    )
    gw.get_summary.return_value = {"data": {"stage_counts": {}}}
    gw.list_requesters.return_value = {"data": {"items": []}}
    gw.list_cost_centers.return_value = {"data": {"items": []}}
    gw.get_purchase_request.return_value = {"data": {"request_number": "179309"}}
    gw.export_purchase_requests.return_value = _pr_ok(
        [{"branch": "01", "request_number": "179309"}]
    )
    with patch.object(tool_bridge, "_PR_GATEWAY", gw), patch.object(
        tool_bridge, "_PR_REQUESTER_IDENTITY"
    ) as ri, patch.object(tool_bridge, "_effective_user", return_value=_User()):
        ri.enrich_payload.side_effect = lambda data, **kw: data
        yield gw


@pytest.fixture
def po_gateway():
    gw = MagicMock()
    gw.get.return_value = {"data": {"items": [{"x": 1}], "total": 1}}
    with patch.object(tool_bridge, "_GATEWAY", gw), patch.object(
        tool_bridge, "_effective_user", return_value=_User()
    ):
        yield gw


def _ok(result):
    return getattr(result, "is_error", getattr(result, "isError", False)) is False


def test_sibling_model_dump_leaks_no_phantom_keys():
    """A payload resolved to the sibling PO model must not inject its
    defaults into the dispatch dict (root cause of the runtime bug)."""
    sibling = PurchaseOrderSearchFilters.model_validate({"branch": ["01"]})
    payload = tool_bridge._payload_dict(sibling)
    assert payload == {"branch": ["01"]}
    assert "late_only" not in payload
    assert "page" not in payload
    assert "page_size" not in payload


def test_pr_search_accepts_minimal_payload_from_sibling_model(pr_gateway):
    """Exact runtime failure of the G2 deploy: union picked the PO model,
    dump leaked `late_only` -> dispatcher 422 for every PR action."""
    model = PurchaseOrderSearchFilters.model_validate(
        {"branch": ["01"], "page": 1, "page_size": 5}
    )
    result = tool_bridge.tool_read("purchase_requests", "search", model)
    assert _ok(result), result
    pr_gateway.list_purchase_requests.assert_called_once()
    _, kwargs = pr_gateway.list_purchase_requests.call_args
    qs = kwargs.get("query_string") or ""
    assert "late_only" not in qs


def test_pr_export_minimal_payload_reaches_gateway(pr_gateway):
    model = PurchaseOrderExportFilters.model_validate({"branch": ["01"]})
    result = tool_bridge.tool_read("purchase_requests", "export", model)
    assert _ok(result), result
    pr_gateway.export_purchase_requests.assert_called_once()


def test_po_export_minimal_payload_reaches_gateway(po_gateway):
    model = PurchaseOrderSearchFilters.model_validate({"branch": ["01"]})
    result = tool_bridge.tool_read("purchase_orders", "export", model)
    assert _ok(result), result
    po_gateway.get.assert_called_once()
    assert po_gateway.get.call_args[0][0] == "/supplies/purchase-orders/export"


def test_pr_actions_reach_dedicated_handlers(pr_gateway):
    model = PurchaseRequestSearchFilters.model_validate({"branch": ["01"]})
    for action in ("search", "summary", "requesters", "cost_centers"):
        result = tool_bridge.tool_read("purchase_requests", action, model)
        assert _ok(result), (action, result)
    ident = PurchaseRequestIdentity.model_validate(
        {"branch": "01", "request_number": "179309"}
    )
    result = tool_bridge.tool_read("purchase_requests", "get", None, ident)
    assert _ok(result), result
    pr_gateway.get_purchase_request.assert_called_once()


def test_user_supplied_keys_still_validated(pr_gateway):
    """Closed vocabulary still fails closed on *real* unknown keys."""
    model = PurchaseRequestExportFilters.model_validate(
        {"branch": ["01"], "sort_by": "request_issue_date"}
    )
    result = tool_bridge.tool_read("purchase_requests", "export", model)
    assert _ok(result), result
    # and a genuine unknown key keeps being rejected at handler level
    result = tool_bridge.tool_read(
        "purchase_requests", "export", {"branch": ["01"], "bogus": 1}
    )
    assert not _ok(result)
