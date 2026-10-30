"""SURI tool bridge — AuthZ parity tests (positive/sibling/negative)."""

from __future__ import annotations

import json

import pytest
from suri_mcp.suri_fixtures import make_context, make_user_ns

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.mcp import tool_bridge


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


class TestGetMyContext:
    def test_positive_returns_declared_capabilities(self, access_context):
        access_context()
        result = tool_bridge.tool_get_my_context()
        data = _payload(result)["data"]
        assert data["subject"] == "user-1"
        assert data["capabilities"] == {"access": True, "manage": False}
        assert data["allowed_units"] == ["01", "02"]
        assert data["mcp"]["catalog_version"] == 1

    def test_negative_anonymous_401(self, anonymous_context):
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_my_context)
        )
        data = _payload(result)
        assert data["success"] is False
        assert data["status_code"] == 401
        assert data["data"]["error_code"] == "unauthenticated"
        # WWW-Authenticate meta envelope present on 401 (list form)
        assert "mcp/www_authenticate" in (result.meta or {})

    def test_negative_service_principal_403(self, monkeypatch):
        ns = make_user_ns(
            permissions=["supplies.access"], principal_type="service"
        )
        monkeypatch.setattr(
            tool_bridge, "require_mcp_context", lambda: make_context(ns)
        )
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_my_context)
        )
        data = _payload(result)
        assert data["status_code"] == 403
        assert data["data"]["error_code"] == "forbidden"


class TestGetCatalog:
    def test_lists_only_implemented_tools(self, access_context):
        access_context()
        result = tool_bridge.tool_get_catalog()
        data = _payload(result)["data"]
        names = {t["name"] for t in data["tools"]}
        assert names == {
            "get_my_context",
            "get_catalog",
            "list_purchase_orders",
            "get_purchase_order",
            "search_supplies_knowledge",
            "get_knowledge_item",
            "list_knowledge_sources",
            "analyze_purchase_orders",
        }
        assert data["mcp"]["catalog_version"] == 1

    def test_requires_identity(self, anonymous_context):
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_catalog)
        )
        assert _payload(result)["status_code"] == 401


class TestListPurchaseOrders:
    def test_positive_calls_bff_with_branch_and_params(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={
            "success": True,
            "data": {"items": [], "total": 0},
        })
        result = tool_bridge.tool_list_purchase_orders(
            branch=["01"], page=2, page_size=10, late_only=True
        )
        body = _payload(result)
        assert body["success"] is True
        call = gw.calls[0]
        assert call["path"] == "/supplies/purchase-orders"
        assert call["access_token"] == "token-abc"
        assert call["params"]["branch"] == ["01"]
        assert call["params"]["late_only"] == "true"
        assert call["params"]["page_size"] == "10"
        # parity: BFF envelope unwrapped to data
        assert body["data"] == {"items": [], "total": 0}
        assert (result.meta or {}).get("delpi/source") == "bff:/purchase-orders"

    def test_sibling_branch_02(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"success": True, "data": {"items": []}})
        tool_bridge.tool_list_purchase_orders(branch=["02"])
        assert gw.calls[0]["params"]["branch"] == ["02"]

    def test_page_size_capped_at_max(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"data": {"items": []}})
        tool_bridge.tool_list_purchase_orders(branch=["01"], page_size=999)
        assert gw.calls[0]["params"]["page_size"] == "100"

    def test_negative_without_supplies_access(
        self, no_access_context, fake_gateway
    ):
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_list_purchase_orders, branch=["01"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_branch_outside_scope(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_list_purchase_orders, branch=["03"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_empty_branch_fail_closed(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_list_purchase_orders, branch=[])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_upstream_404_maps_not_found(self, access_context, fake_gateway):
        access_context()
        fake_gateway(
            error=DelpiApiGatewayError(
                "api-delpi client error", status_code=404
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_list_purchase_orders, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 404
        assert body["data"]["error_code"] == "not_found"

    def test_upstream_5xx_maps_upstream(self, access_context, fake_gateway):
        access_context()
        fake_gateway(
            error=DelpiApiGatewayError(
                "api-delpi server error", status_code=503
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_list_purchase_orders, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 502
        assert body["data"]["error_code"] == "upstream"


class TestGetPurchaseOrder:
    def test_positive_detail(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"data": {"branch": "01", "order_number": "9"}})
        result = tool_bridge.tool_get_purchase_order("01", "9")
        assert _payload(result)["success"] is True
        assert gw.calls[0]["path"] == "/supplies/purchase-orders/01/9"

    def test_negative_invalid_identity(self, access_context):
        access_context()
        result = tool_bridge.tool_get_purchase_order("  ", "9")
        assert _payload(result)["status_code"] == 422

    def test_negative_branch_forbidden(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_purchase_order, "03", "9")
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []


def _call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return exc
    raise AssertionError("expected exception")
