"""Smoke — rota de detalhe de pedido de compra em aberto (Suprimentos)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.responses import error_response
from app.interface.http.routes.supplies.purchase_orders_router import (
    get_supplies_purchase_order,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ROUTER = "app.interface.http.routes.supplies.purchase_orders_router"


@patch(f"{_ROUTER}.branch_access_error", return_value=None)
@patch(f"{_ROUTER}.build_get_supplies_purchase_order_use_case")
def test_get_supplies_purchase_order_meta(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "branch": "01",
                "order_number": "000123",
                "items": [
                    {
                        "order_item": "0001",
                        "supplier_code": "A001",
                        "receipts": [],
                    }
                ],
            }
        )
    )
    response = get_supplies_purchase_order(branch="01", order_number="000123")
    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_supplies_purchase_order",
        shape="product_snapshot",
    )
    assert body["data"]["branch"] == "01"
    assert "supplier" not in body["data"]
    assert body["data"]["items"][0]["supplier_code"] == "A001"


@patch(f"{_ROUTER}.branch_access_error", return_value=None)
@patch(f"{_ROUTER}.build_get_supplies_purchase_order_use_case")
def test_get_supplies_purchase_order_not_found(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=None))
    response = get_supplies_purchase_order(branch="01", order_number="999999")
    body = body_json(response)
    assert response.status_code == 404
    assert body["success"] is False
    assert body["data"] is None


@patch(f"{_ROUTER}.branch_access_error")
@patch(f"{_ROUTER}.build_get_supplies_purchase_order_use_case")
def test_get_supplies_purchase_order_forbidden_branch(mock_build, mock_gate) -> None:
    mock_gate.return_value = error_response(
        "Sem permissão para a filial.",
        status_code=403,
        code="FORBIDDEN",
    )
    response = get_supplies_purchase_order(branch="02", order_number="000123")
    assert response.status_code == 403
    mock_build.assert_not_called()


@patch(f"{_ROUTER}.branch_access_error", return_value=None)
@patch(f"{_ROUTER}.build_get_supplies_purchase_order_use_case")
def test_get_supplies_purchase_order_invalid_input(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(side_effect=ValueError("branch and order_number are required"))
    )
    response = get_supplies_purchase_order(branch="01", order_number="   ")
    assert response.status_code == 422
