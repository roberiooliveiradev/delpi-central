from __future__ import annotations

import pytest
import responses

from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
    PurchaseRequestsGatewayError,
)


@responses.activate
def test_list_forwards_bearer_and_query():
    responses.add(
        responses.GET,
        "http://pr-api.test/purchase-requests",
        json={"success": True, "data": {"items": [], "total": 0}},
        status=200,
    )
    gateway = PurchaseRequestsGateway(
        base_url="http://pr-api.test",
        timeout_seconds=2.0,
        caller_app="supplies-api",
    )
    payload = gateway.list_purchase_requests(
        access_token="tok-1",
        query_string="branch=01&overall_stage=awaiting_order",
    )
    assert payload["data"]["total"] == 0
    assert responses.calls[0].request.headers["Authorization"] == "Bearer tok-1"
    assert responses.calls[0].request.headers["X-Delpi-Caller-App"] == "supplies-api"
    assert "branch=01" in (responses.calls[0].request.url or "")


@responses.activate
def test_get_detail_positive():
    responses.add(
        responses.GET,
        "http://pr-api.test/purchase-requests/01/SC001",
        json={"success": True, "data": {"header": {"request_number": "SC001"}}},
        status=200,
    )
    gateway = PurchaseRequestsGateway(base_url="http://pr-api.test", timeout_seconds=2.0)
    payload = gateway.get_purchase_request(
        access_token="tok",
        branch="01",
        request_number="SC001",
    )
    assert payload["data"]["header"]["request_number"] == "SC001"


@responses.activate
def test_list_forbidden_propagates_status():
    responses.add(
        responses.GET,
        "http://pr-api.test/purchase-requests",
        json={"success": False, "message": "Sem permissão"},
        status=403,
    )
    gateway = PurchaseRequestsGateway(base_url="http://pr-api.test", timeout_seconds=2.0)
    with pytest.raises(PurchaseRequestsGatewayError) as exc:
        gateway.list_purchase_requests(access_token="tok", params={"branch": "01"})
    assert exc.value.status_code == 403


@responses.activate
def test_count_open_sibling_sums_stages():
    for _stage in PurchaseRequestsGateway.OPEN_STAGES:
        responses.add(
            responses.GET,
            "http://pr-api.test/purchase-requests",
            json={"success": True, "data": {"items": [], "total": 2}},
            status=200,
        )
    gateway = PurchaseRequestsGateway(base_url="http://pr-api.test", timeout_seconds=2.0)
    assert gateway.count_open_requests(access_token="tok", branch="01") == 2 * len(
        PurchaseRequestsGateway.OPEN_STAGES
    )
    assert len(responses.calls) == len(PurchaseRequestsGateway.OPEN_STAGES)
