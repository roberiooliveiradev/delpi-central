"""Smoke — rotas purchase orders list (Suprimentos)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.supplies.purchase_orders_router import (
    export_supplies_purchase_orders_route,
    list_supplies_purchase_orders_route,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ROUTER = "app.interface.http.routes.supplies.purchase_orders_router"


@patch(f"{_ROUTER}.branches_access_error", return_value=None)
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
                "summary": {
                    "total_lines": 0,
                    "total_open_value": 0,
                    "late_lines": 0,
                    "on_time_lines": 0,
                    "no_date_lines": 0,
                },
            }
        )
    )
    response = list_supplies_purchase_orders_route(
        branch=["02"],
        page=1,
        page_size=50,
        order_number=None,
        product_code=None,
        supplier_code=None,
        expected_delivery_from=None,
        expected_delivery_to=None,
        late_only=False,
        sort_by=None,
        sort_dir=None,
    )
    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="list_supplies_purchase_orders",
        shape="paged_list",
    )
    data = body.get("data") or body
    summary = data["summary"]
    assert summary["total_lines"] == 0
    assert summary["total_open_value"] == 0
    assert summary["late_lines"] == 0
    assert summary["on_time_lines"] == 0
    assert summary["no_date_lines"] == 0
    assert (
        summary["total_lines"]
        == summary["late_lines"] + summary["on_time_lines"] + summary["no_date_lines"]
    )
    mock_build.return_value.execute.assert_called_once()
    assert mock_build.return_value.execute.call_args.kwargs["branches"] == ["02"]


@patch(f"{_ROUTER}.branches_access_error", return_value=None)
@patch(f"{_ROUTER}.build_list_supplies_purchase_orders_use_case")
def test_export_supplies_purchase_orders_meta(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        export=MagicMock(
            return_value={
                "items": [{"order_number": "0001"}],
                "total": 1,
            }
        )
    )
    response = export_supplies_purchase_orders_route(
        branch=["01", "02"],
        order_number=None,
        product_code=None,
        supplier_code=None,
        expected_delivery_from=None,
        expected_delivery_to=None,
        late_only=False,
        sort_by="open_value",
        sort_dir="desc",
    )
    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="export_supplies_purchase_orders",
        shape="document_export",
    )
    data = body.get("data") or body
    assert data["total"] == 1
    assert "page" not in data
    mock_build.return_value.export.assert_called_once()
    assert mock_build.return_value.export.call_args.kwargs["branches"] == ["01", "02"]
    assert mock_build.return_value.export.call_args.kwargs["sort_by"] == "open_value"


@patch(f"{_ROUTER}.branches_access_error", return_value=None)
@patch(f"{_ROUTER}.build_list_supplies_purchase_orders_use_case")
def test_list_invalid_sort_returns_422(mock_build, _branch_gate) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(side_effect=ValueError("Invalid sort_by"))
    )
    response = list_supplies_purchase_orders_route(
        branch=["01"],
        page=1,
        page_size=50,
        order_number=None,
        product_code=None,
        supplier_code=None,
        expected_delivery_from=None,
        expected_delivery_to=None,
        late_only=False,
        sort_by="not_a_field",
        sort_dir="asc",
    )
    assert response.status_code == 422
    mock_build.return_value.execute.assert_called_once()
