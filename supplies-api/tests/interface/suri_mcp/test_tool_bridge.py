"""SURI semantic tool bridge — AuthZ parity + dispatch validation.

Covers the rev.2 surface: ``get_context``, ``read``, ``analyze``,
``knowledge`` dispatchers with closed discriminators, parity with the
eight legacy capabilities, and semantic validation negatives.
"""

from __future__ import annotations

import json

import pytest
from suri_mcp.suri_fixtures import make_context, make_user_ns

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.mcp import tool_bridge


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


class TestGetContext:
    def test_context_positive_returns_declared_capabilities(
        self, access_context
    ):
        access_context()
        result = tool_bridge.tool_get_context("context")
        data = _payload(result)["data"]
        assert data["subject"] == "user-1"
        assert data["capabilities"] == {"access": True, "manage": False}
        assert data["allowed_units"] == ["01", "02"]
        assert data["mcp"]["catalog_version"] == 5

    def test_catalog_lists_semantic_surface(self, access_context):
        access_context()
        result = tool_bridge.tool_get_context("catalog")
        data = _payload(result)["data"]
        names = {t["name"] for t in data["tools"]}
        assert names == {
            "get_context",
            "read",
            "analyze",
            "knowledge",
            "execute",
        }
        assert data["mcp"]["catalog_version"] == 5
        caps = data["capabilities"]
        assert "purchase_orders" in caps["read"]["entities"]
        assert caps["analyze"]["analyses"] == [
            "purchase_orders_summary",
            "supplier_creation_preview",
        ]
        assert set(caps["read"]["entities"]) == {
            "purchase_orders",
            "purchase_requests",
            "suppliers",
            "postal_codes",
        }
        assert caps["knowledge"]["actions"] == ["get", "search", "sources"]
        assert caps["execute"]["entities"]["suppliers"]["actions"] == [
            "create",
            "update",
        ]

    def test_negative_anonymous_401(self, anonymous_context):
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_context, "context")
        )
        data = _payload(result)
        assert data["success"] is False
        assert data["status_code"] == 401
        assert data["data"]["error_code"] == "unauthenticated"
        assert "mcp/www_authenticate" in (result.meta or {})

    def test_negative_service_principal_403(self, monkeypatch):
        ns = make_user_ns(
            permissions=["supplies.access"], principal_type="service"
        )
        monkeypatch.setattr(
            tool_bridge, "require_mcp_context", lambda: make_context(ns)
        )
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_get_context, "context")
        )
        assert _payload(result)["status_code"] == 403

    def test_negative_unknown_action(self, access_context):
        access_context()
        result = tool_bridge.tool_get_context("bogus")
        body = _payload(result)
        assert body["status_code"] == 422
        assert body["data"]["error_code"] == "validation"


class TestReadSearchParity:
    """Parity with legacy list_purchase_orders."""

    def _search(self, **filters):
        return tool_bridge.tool_read(
            "purchase_orders", "search", filters=filters
        )

    def test_positive_calls_bff_with_branch_and_params(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={
            "success": True,
            "data": {"items": [], "total": 0},
        })
        result = self._search(
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
        assert body["data"] == {"items": [], "total": 0}
        assert (result.meta or {}).get("delpi/source") == (
            "bff:/purchase-orders"
        )

    def test_sibling_branch_02(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"success": True, "data": {"items": []}})
        self._search(branch=["02"])
        assert gw.calls[0]["params"]["branch"] == ["02"]

    def test_page_size_capped_at_max(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"data": {"items": []}})
        self._search(branch=["01"], page_size=999)
        assert gw.calls[0]["params"]["page_size"] == "100"

    def test_negative_without_supplies_access(
        self, no_access_context, fake_gateway
    ):
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_branch_outside_scope(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["03"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_empty_branch_fail_closed(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=[])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_missing_branch_fail_closed(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(_call(self._search))
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
            _call(self._search, branch=["01"])
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
            _call(self._search, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 502
        assert body["data"]["error_code"] == "upstream"


class TestReadGetParity:
    """Parity with legacy get_purchase_order."""

    def _get(self, **identity):
        return tool_bridge.tool_read(
            "purchase_orders", "get", identity=identity
        )

    def test_positive_detail(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(
            payload={"data": {"branch": "01", "order_number": "9"}}
        )
        result = self._get(branch="01", order_number="9")
        assert _payload(result)["success"] is True
        assert gw.calls[0]["path"] == "/supplies/purchase-orders/01/9"

    def test_negative_missing_identity(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders", "get", identity={"branch": "01"}
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_blank_identity(self, access_context):
        access_context()
        result = self._get(branch="  ", order_number="9")
        assert _payload(result)["status_code"] == 422

    def test_negative_branch_forbidden(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(self._get, branch="03", order_number="9")
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []


class TestSemanticValidation:
    """Closed discriminators — unknown combos are 422, never forwarded."""

    def test_unknown_entity(self, access_context):
        access_context()
        result = tool_bridge.tool_read("inventory", "search", filters={})
        assert _payload(result)["status_code"] == 422

    def test_unregistered_entity_still_closed(self, access_context):
        access_context()
        result = tool_bridge.tool_read("invoices", "search")
        assert _payload(result)["status_code"] == 422

    def test_unknown_action(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders", "delete", filters={"branch": ["01"]}
        )
        assert _payload(result)["status_code"] == 422

    def test_unknown_filter_key_rejected(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.tool_read(
            "purchase_orders",
            "search",
            filters={"branch": ["01"], "raw_sql": "DROP TABLE"},
        )
        assert _payload(result)["status_code"] == 422
        assert gw.calls == []

    def test_identity_rejected_on_search(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders",
            "search",
            filters={"branch": ["01"]},
            identity={"branch": "01", "order_number": "1"},
        )
        assert _payload(result)["status_code"] == 422

    def test_filters_rejected_on_get(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders",
            "get",
            filters={"branch": ["01"]},
            identity={"branch": "01", "order_number": "1"},
        )
        assert _payload(result)["status_code"] == 422

    def test_unknown_identity_key(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders",
            "get",
            identity={"branch": "01", "order_number": "1", "admin": True},
        )
        assert _payload(result)["status_code"] == 422


def _call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return exc
    raise AssertionError("expected exception")
