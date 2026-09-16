"""Smoke — rotas purchase request lines (Suprimentos)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.supplies.purchase_requests_router import (
    get_supplies_purchase_request_lines_route,
    list_supplies_purchase_request_lines_route,
    list_supplies_purchase_request_recent_linked_orders_route,
    list_supplies_purchase_request_recent_linked_receipts_route,
    router,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ROUTER = "app.interface.http.routes.supplies.purchase_requests_router"


def _get_route_endpoint(path: str) -> str:
    for route in router.routes:
        if getattr(route, "path", None) != path:
            continue
        methods = getattr(route, "methods", None) or set()
        if "GET" not in methods:
            continue
        return getattr(route.endpoint, "__name__", "")
    raise AssertionError(f"GET {path} is not registered")


def test_list_lines_http_binds_list_handler_not_helper() -> None:
    assert (
        _get_route_endpoint("/supplies/purchase-requests/lines")
        == "list_supplies_purchase_request_lines_route"
    )


def test_export_lines_http_binds_export_handler() -> None:
    assert (
        _get_route_endpoint("/supplies/purchase-requests/lines/export")
        == "export_supplies_purchase_request_lines_route"
    )


def test_lines_helper_is_not_an_http_route() -> None:
    names = {
        getattr(route.endpoint, "__name__", "")
        for route in router.routes
        if "GET" in (getattr(route, "methods", None) or set())
    }
    assert "_lines_kwargs" not in names


@patch(f"{_ROUTER}.purchase_requests_branches_access_error", return_value=None)
@patch(f"{_ROUTER}.build_list_supplies_purchase_request_lines_use_case")
def test_list_supplies_purchase_request_lines_meta(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
            }
        )
    )
    response = list_supplies_purchase_request_lines_route(
        branch=["02"],
        date_from=None,
        date_to=None,
        cost_centers=None,
        request_number=None,
        requester_protheus_user_id=None,
        product_code=None,
        supplier_code=None,
        order_number=None,
        page=1,
        page_size=50,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_supplies_purchase_request_lines",
        shape="paged_list",
    )


@patch(f"{_ROUTER}.purchase_requests_branch_access_error", return_value=None)
@patch(f"{_ROUTER}.build_get_supplies_purchase_request_lines_use_case")
def test_get_supplies_purchase_request_lines_meta(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"lines": []})
    )
    response = get_supplies_purchase_request_lines_route(
        branch="02",
        request_number="164708",
        date_from=None,
        date_to=None,
        cost_centers=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_purchase_request_lines",
        shape="list",
    )


@patch(f"{_ROUTER}.build_list_supplies_purchase_request_recent_linked_orders_use_case")
def test_list_supplies_purchase_request_recent_linked_orders_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "after_recno": 0,
                "limit": 100,
                "max_recno": 0,
            }
        )
    )
    response = list_supplies_purchase_request_recent_linked_orders_route(
        after_recno=0,
        limit=100,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_supplies_purchase_request_recent_linked_orders",
        shape="list",
    )


@patch(f"{_ROUTER}.build_list_supplies_purchase_request_recent_linked_receipts_use_case")
def test_list_supplies_purchase_request_recent_linked_receipts_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "after_recno": 0,
                "limit": 100,
                "max_recno": 0,
            }
        )
    )
    response = list_supplies_purchase_request_recent_linked_receipts_route(
        after_recno=0,
        limit=100,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_supplies_purchase_request_recent_linked_receipts",
        shape="list",
    )
