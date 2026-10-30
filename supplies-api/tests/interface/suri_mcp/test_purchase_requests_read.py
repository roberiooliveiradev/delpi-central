"""SURI purchase_requests read parity + PO export (rev.5).

Covers the six SC actions (search/summary/requesters/cost_centers/
get/export) and the PO export action: closed vocabularies, canonical
authorization (supplies.access + unit scope), query-string forwarding
to the owner gateway, requester enrichment reuse, and the DECISION-G1
export contract (JSON dataset + artifact metadata, never binary).
"""

from __future__ import annotations

import json

import pytest
from suri_mcp.suri_fixtures import make_context, make_user_ns

from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGatewayError,
)
from app.interfaces.mcp import tool_bridge


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


def _call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return exc
    raise AssertionError("expected exception")


class FakePrGateway:
    """Captures calls and returns a canned purchase-requests payload."""

    def __init__(self, payload=None, error=None):
        self.payload = payload if payload is not None else {"data": {}}
        self.error = error
        self.calls: list[dict] = []

    def _record(self, method: str, **kwargs):
        self.calls.append({"method": method, **kwargs})
        if self.error is not None:
            raise self.error
        return self.payload

    def list_purchase_requests(self, *, access_token, query_string=None, **kw):
        return self._record(
            "list", access_token=access_token, query_string=query_string
        )

    def get_summary(self, *, access_token, query_string=None, **kw):
        return self._record(
            "summary", access_token=access_token, query_string=query_string
        )

    def list_requesters(self, *, access_token, query_string=None, **kw):
        return self._record(
            "requesters",
            access_token=access_token,
            query_string=query_string,
        )

    def list_cost_centers(self, *, access_token, query_string=None, **kw):
        return self._record(
            "cost_centers",
            access_token=access_token,
            query_string=query_string,
        )

    def get_purchase_request(
        self, *, access_token, branch, request_number, query_string=None, **kw
    ):
        return self._record(
            "get",
            access_token=access_token,
            branch=branch,
            request_number=request_number,
            query_string=query_string,
        )

    def export_purchase_requests(
        self, *, access_token, query_string=None, **kw
    ):
        return self._record(
            "export", access_token=access_token, query_string=query_string
        )


class FakeRequesterIdentity:
    """Marks payloads as enriched without hitting Core."""

    def __init__(self):
        self.calls = 0

    def enrich_payload(self, data, *, access_token):
        self.calls += 1
        if isinstance(data, dict):
            data = dict(data)
            data["enriched"] = True
        return data


@pytest.fixture()
def fake_pr_gateway(monkeypatch):
    def _install(payload=None, error=None) -> FakePrGateway:
        gw = FakePrGateway(payload=payload, error=error)
        monkeypatch.setattr(tool_bridge, "_PR_GATEWAY", gw)
        return gw

    return _install


@pytest.fixture()
def fake_requester_identity(monkeypatch):
    identity = FakeRequesterIdentity()
    monkeypatch.setattr(tool_bridge, "_PR_REQUESTER_IDENTITY", identity)
    return identity


class TestPurchaseRequestSearch:
    def _search(self, **filters):
        return tool_bridge.tool_read(
            "purchase_requests", "search", filters=filters
        )

    def test_positive_forwards_closed_filters(
        self, access_context, fake_pr_gateway, fake_requester_identity
    ):
        access_context()
        gw = fake_pr_gateway(payload={"data": {"items": [], "total": 0}})
        result = self._search(
            branch=["01", "02"],
            date_from="2026-01-01",
            date_to="2026-10-31",
            request_number="SC123",
            requester_user_id=["U1", "U2"],
            cost_center=["CC01"],
            product_code="MP1",
            supplier_code="F1",
            order_number="9",
            overall_stage=["awaiting_order"],
            sort_by="issue_date",
            sort_dir="desc",
            page=2,
            page_size=10,
        )
        body = _payload(result)
        assert body["success"] is True
        call = gw.calls[0]
        assert call["method"] == "list"
        assert call["access_token"] == "token-abc"
        qs = call["query_string"]
        assert "branch=01" in qs and "branch=02" in qs
        assert "requester_user_id=U1" in qs
        assert "requester_user_id=U2" in qs
        assert "cost_center=CC01" in qs
        assert "overall_stage=awaiting_order" in qs
        assert "page=2" in qs and "page_size=10" in qs
        assert body["data"]["enriched"] is True
        assert (result.meta or {}).get("delpi/source") == (
            "bff:/purchase-requests"
        )

    def test_page_size_capped(
        self, access_context, fake_pr_gateway, fake_requester_identity
    ):
        access_context()
        gw = fake_pr_gateway(payload={"data": {}})
        self._search(branch=["01"], page_size=999)
        assert "page_size=100" in gw.calls[0]["query_string"]

    def test_negative_no_access(self, no_access_context, fake_pr_gateway):
        gw = fake_pr_gateway()
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_branch_outside_scope(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        gw = fake_pr_gateway()
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["03"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_missing_branch(self, access_context, fake_pr_gateway):
        access_context()
        gw = fake_pr_gateway()
        result = tool_bridge.handle_tool_error(_call(self._search))
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_unknown_filter_key(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        gw = fake_pr_gateway()
        result = self._search(branch=["01"], raw_sql="DROP TABLE")
        assert _payload(result)["status_code"] == 422
        assert gw.calls == []

    def test_negative_identity_rejected(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "search",
            filters={"branch": ["01"]},
            identity={"branch": "01", "request_number": "1"},
        )
        assert _payload(result)["status_code"] == 422

    def test_upstream_404_maps_not_found(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        fake_pr_gateway(
            error=PurchaseRequestsGatewayError(
                "not found", status_code=404, payload={"message": "nada"}
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 404
        assert body["data"]["error_code"] == "not_found"

    def test_upstream_5xx_maps_upstream(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        fake_pr_gateway(
            error=PurchaseRequestsGatewayError(
                "upstream error", status_code=503
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 502
        assert body["data"]["error_code"] == "upstream"

    def test_upstream_403_maps_forbidden(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        fake_pr_gateway(
            error=PurchaseRequestsGatewayError(
                "forbidden", status_code=403
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        assert _payload(result)["status_code"] == 403

    def test_gateway_timeout_maps_upstream(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        fake_pr_gateway(
            error=PurchaseRequestsGatewayError(
                "purchase-requests-api timeout"
            )
        )
        result = tool_bridge.handle_tool_error(
            _call(self._search, branch=["01"])
        )
        body = _payload(result)
        assert body["status_code"] == 502
        assert body["data"]["error_code"] == "upstream"


class TestPurchaseRequestSummary:
    def test_positive(self, access_context, fake_pr_gateway):
        access_context()
        gw = fake_pr_gateway(
            payload={"data": {"stage_counts": {"awaiting_order": 3}}}
        )
        result = tool_bridge.tool_read(
            "purchase_requests",
            "summary",
            filters={
                "branch": ["01"],
                "cost_center": ["CC1"],
                "overall_stage": ["awaiting_order"],
            },
        )
        body = _payload(result)
        assert body["success"] is True
        call = gw.calls[0]
        assert call["method"] == "summary"
        assert "cost_center=CC1" in call["query_string"]
        assert body["data"]["stage_counts"]["awaiting_order"] == 3

    def test_negative_sort_rejected(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "summary",
            filters={"branch": ["01"], "sort_by": "issue_date"},
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_pagination_rejected(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "summary",
            filters={"branch": ["01"], "page": 2},
        )
        assert _payload(result)["status_code"] == 422


class TestPurchaseRequestFacets:
    def test_requesters_positive(
        self, access_context, fake_pr_gateway, fake_requester_identity
    ):
        access_context()
        gw = fake_pr_gateway(payload={"data": {"items": []}})
        result = tool_bridge.tool_read(
            "purchase_requests",
            "requesters",
            filters={"branch": ["01"], "cost_center": ["CC1"]},
        )
        body = _payload(result)
        assert body["success"] is True
        assert gw.calls[0]["method"] == "requesters"
        assert body["data"]["enriched"] is True

    def test_requesters_rejects_requester_filter(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "requesters",
            filters={"branch": ["01"], "requester_user_id": ["U1"]},
        )
        assert _payload(result)["status_code"] == 422

    def test_cost_centers_positive(self, access_context, fake_pr_gateway):
        access_context()
        gw = fake_pr_gateway(payload={"data": {"items": []}})
        result = tool_bridge.tool_read(
            "purchase_requests",
            "cost_centers",
            filters={"branch": ["02"]},
        )
        assert _payload(result)["success"] is True
        assert gw.calls[0]["method"] == "cost_centers"

    def test_cost_centers_rejects_self_filter(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "cost_centers",
            filters={"branch": ["01"], "cost_center": ["CC1"]},
        )
        assert _payload(result)["status_code"] == 422


class TestPurchaseRequestGet:
    def _get(self, identity=None, filters=None):
        return tool_bridge.tool_read(
            "purchase_requests",
            "get",
            identity=identity,
            filters=filters,
        )

    def test_positive(
        self, access_context, fake_pr_gateway, fake_requester_identity
    ):
        access_context()
        gw = fake_pr_gateway(payload={"data": {"request_number": "SC1"}})
        result = self._get(
            identity={"branch": "01", "request_number": "SC1"},
            filters={"cost_center": ["CC1"], "date_from": "2026-01-01"},
        )
        body = _payload(result)
        assert body["success"] is True
        call = gw.calls[0]
        assert call["method"] == "get"
        assert call["branch"] == "01"
        assert call["request_number"] == "SC1"
        assert "cost_center=CC1" in call["query_string"]
        assert body["data"]["enriched"] is True

    def test_negative_missing_identity(self, access_context):
        access_context()
        result = self._get(identity={"branch": "01"})
        assert _payload(result)["status_code"] == 422

    def test_negative_context_outside_owner_contract(self, access_context):
        access_context()
        result = self._get(
            identity={"branch": "01", "request_number": "SC1"},
            filters={"overall_stage": ["awaiting_order"]},
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_branch_outside_scope(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        gw = fake_pr_gateway()
        result = tool_bridge.handle_tool_error(
            _call(
                self._get,
                identity={"branch": "03", "request_number": "SC1"},
            )
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []


class TestPurchaseRequestExport:
    def _export(self, **filters):
        return tool_bridge.tool_read(
            "purchase_requests", "export", filters=filters
        )

    def test_positive_json_dataset(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        gw = fake_pr_gateway(
            payload={"data": {"items": [{"request_number": "SC1"}]}}
        )
        result = self._export(
            branch=["01"], date_from="2026-01-01", sort_by="issue_date"
        )
        body = _payload(result)
        assert body["success"] is True
        data = body["data"]
        assert data["items"] == [{"request_number": "SC1"}]
        assert data["export"]["format"] == "json"
        assert data["export"]["row_count"] == 1
        assert set(data["export"]["portal_file_formats"]) == {"csv", "xlsx"}
        assert gw.calls[0]["method"] == "export"
        assert (result.meta or {}).get("delpi/source") == (
            "bff:/purchase-requests/export"
        )

    def test_negative_empty_branch_fail_closed(
        self, access_context, fake_pr_gateway
    ):
        access_context()
        gw = fake_pr_gateway()
        result = tool_bridge.handle_tool_error(
            _call(self._export, branch=[])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_pagination_rejected(self, access_context):
        access_context()
        result = self._export(branch=["01"], page=2)
        assert _payload(result)["status_code"] == 422

    def test_negative_format_key_rejected(self, access_context):
        access_context()
        result = self._export(branch=["01"], format="xlsx")
        assert _payload(result)["status_code"] == 422


class TestPurchaseOrderExport:
    def _export(self, **filters):
        return tool_bridge.tool_read(
            "purchase_orders", "export", filters=filters
        )

    def test_positive_json_dataset(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(
            payload={
                "success": True,
                "data": {"items": [{"order_number": "9"}]},
            }
        )
        result = self._export(
            branch=["01"], late_only=True, supplier_code="F1"
        )
        body = _payload(result)
        assert body["success"] is True
        call = gw.calls[0]
        assert call["path"] == "/supplies/purchase-orders/export"
        assert call["params"]["branch"] == ["01"]
        assert call["params"]["late_only"] == "true"
        assert call["params"]["supplier_code"] == "F1"
        assert "page" not in call["params"]
        assert "page_size" not in call["params"]
        data = body["data"]
        assert data["export"]["format"] == "json"
        assert data["export"]["row_count"] == 1
        assert data["export"]["portal_file_formats"] == ["xlsx"]
        assert (result.meta or {}).get("delpi/source") == (
            "bff:/purchase-orders/export"
        )

    def test_negative_no_access(self, no_access_context, fake_gateway):
        gw = fake_gateway(payload={"data": {}})
        result = tool_bridge.handle_tool_error(
            _call(self._export, branch=["01"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_branch_outside_scope(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway()
        result = tool_bridge.handle_tool_error(
            _call(self._export, branch=["03"])
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_pagination_rejected(self, access_context):
        access_context()
        result = self._export(branch=["01"], page_size=50)
        assert _payload(result)["status_code"] == 422

    def test_negative_identity_rejected(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders",
            "export",
            filters={"branch": ["01"]},
            identity={"branch": "01", "order_number": "9"},
        )
        assert _payload(result)["status_code"] == 422


class TestCrossEntityIsolation:
    """Sibling isolation — vocabularies stay closed per entity."""

    def test_sc_filter_rejected_on_po(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_orders",
            "search",
            filters={"branch": ["01"], "overall_stage": ["x"]},
        )
        assert _payload(result)["status_code"] == 422

    def test_po_filter_rejected_on_sc(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "search",
            filters={"branch": ["01"], "late_only": True},
        )
        assert _payload(result)["status_code"] == 422

    def test_po_identity_rejected_on_sc_get(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "get",
            identity={"branch": "01", "order_number": "9"},
        )
        assert _payload(result)["status_code"] == 422

    def test_sc_actions_rejected_on_po(self, access_context):
        access_context()
        for action in ("summary", "requesters", "cost_centers"):
            result = tool_bridge.tool_read(
                "purchase_orders",
                action,
                filters={"branch": ["01"]},
            )
            assert _payload(result)["status_code"] == 422

    def test_po_search_rejected_on_sc(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "purchase_requests",
            "search_by_tax_id",
            filters={"tax_id": "1"},
        )
        assert _payload(result)["status_code"] == 422
