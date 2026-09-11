"""Smoke — rotas purchase orders list (Suprimentos)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.supplies.purchase_orders_router import (
    list_supplies_purchase_orders_route,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ROUTER = "app.interface.http.routes.supplies.purchase_orders_router"


@patch(f"{_ROUTER}.branch_access_error", return_value=None)
@patch(f"{_ROUTER}.build_list_supplies_purchase_orders_use_case")
def test_list_supplies_purchase_orders_meta(mock_build, _branch_gate) -> None:
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
    response = list_supplies_purchase_orders_route(
        branch="02",
        page=1,
        page_size=50,
        order_number=None,
        product_code=None,
        supplier_code=None,
        expected_delivery_from=None,
        expected_delivery_to=None,
        late_only=False,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_supplies_purchase_orders",
        shape="paged_list",
    )
