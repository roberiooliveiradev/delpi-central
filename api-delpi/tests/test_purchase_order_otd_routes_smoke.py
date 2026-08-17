"""Smoke — família OTD pedidos de compra (MP)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.interface.http.routes.supplies.supplies_router import (
    get_supplies_purchase_order_otd,
    get_supplies_purchase_order_otd_panel,
    get_supplies_purchase_order_otd_series,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_SUPPLIES = "app.interface.http.routes.supplies.supplies_router"


@patch(f"{_SUPPLIES}.build_get_purchase_order_otd_use_case")
def test_purchase_order_otd_returns_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "product_type": "MP",
                "total_lines": 0,
                "purchase_order_otd_pct": None,
            }
        )
    )
    response = get_supplies_purchase_order_otd(
        branch=None,
        start_date=None,
        end_date=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_purchase_order_otd",
        shape="scalar",
    )


@patch(f"{_SUPPLIES}.build_get_purchase_order_otd_series_use_case")
def test_purchase_order_otd_series_returns_meta(mock_build) -> None:
    result = MagicMock()
    result.to_dict.return_value = {"points": [], "granularity": "month"}
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))

    response = get_supplies_purchase_order_otd_series(
        granularity="month",
        start_date=None,
        end_date=None,
        branch=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_purchase_order_otd_series",
        shape="scalar",
    )


@patch(f"{_SUPPLIES}.build_get_purchase_order_otd_panel_use_case")
def test_purchase_order_otd_panel_returns_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "summary": {"total_lines": 0},
                "lines": {"items": [], "total": 0, "page": 1, "page_size": 20},
            }
        )
    )
    response = get_supplies_purchase_order_otd_panel(
        branch=None,
        start_date=None,
        end_date=None,
        status=None,
        page=1,
        page_size=20,
        sort_by=None,
        sort_dir="asc",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_supplies_purchase_order_otd_panel",
        shape="paged_list",
    )
