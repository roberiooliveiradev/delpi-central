"""Smoke — rotas purchase request lines (Suprimentos)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.supplies.purchase_requests_router import (
    get_supplies_purchase_request_lines_route,
    list_supplies_purchase_request_lines_route,
    list_supplies_purchase_request_recent_linked_orders_route,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ROUTER = "app.interface.http.routes.supplies.purchase_requests_router"


@patch(f"{_ROUTER}.purchase_requests_branch_access_error", return_value=None)
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
        branch="02",
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
