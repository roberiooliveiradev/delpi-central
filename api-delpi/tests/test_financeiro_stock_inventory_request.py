"""Request validation: competence → snapshot date, filters, pagination."""

from __future__ import annotations

import pytest

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)


def test_period_maps_to_last_calendar_day():
    request = StockInventoryQueryRequest.from_query(period="2026-08")
    assert request.reference_date() == "20260831"
    assert request.reference_date_iso() == "2026-08-31"


def test_period_september_and_october():
    assert (
        StockInventoryQueryRequest.from_query(period="2026-09").reference_date()
        == "20260930"
    )
    assert (
        StockInventoryQueryRequest.from_query(period="2026-10").reference_date()
        == "20261031"
    )


def test_leap_year_february():
    request = StockInventoryQueryRequest.from_query(period="2028-02")
    assert request.reference_date() == "20280229"
    assert (
        StockInventoryQueryRequest.from_query(period="2027-02").reference_date()
        == "20270228"
    )


def test_period_required_and_format():
    for bad in (None, "", "2026-9", "2026/09", "2026-13", "2026-00", "abc"):
        with pytest.raises(ValueError):
            StockInventoryQueryRequest.from_query(period=bad)


def test_branch_scope_validation():
    assert (
        StockInventoryQueryRequest.from_query(
            period="2026-08", branch="all"
        ).requested_branches()
        == ("01", "02")
    )
    assert (
        StockInventoryQueryRequest.from_query(
            period="2026-08", branch="02"
        ).requested_branches()
        == ("02",)
    )
    # PT alias normalizes to all.
    assert (
        StockInventoryQueryRequest.from_query(
            period="2026-08", branch="todas"
        ).branch
        == "all"
    )
    with pytest.raises(ValueError):
        StockInventoryQueryRequest.from_query(period="2026-08", branch="99")


def test_report_scope_maps_product_types():
    all_products = StockInventoryQueryRequest.from_query(period="2026-08")
    assert all_products.report_scope == "all_products"
    assert all_products.product_types() is None
    mp = StockInventoryQueryRequest.from_query(
        period="2026-08", report_scope="mp_pi_pa"
    )
    assert mp.product_types() == ("MP", "PI", "PA")
    with pytest.raises(ValueError):
        StockInventoryQueryRequest.from_query(
            period="2026-08", report_scope="official_p7"
        )


def test_warehouse_and_pagination():
    request = StockInventoryQueryRequest.from_query(
        period="2026-08", warehouse="01", page=0, page_size=200
    )
    assert request.warehouse == "01"
    assert request.page == 1  # clamped to minimum
    with pytest.raises(ValueError):
        StockInventoryQueryRequest.from_query(
            period="2026-08", warehouse="x" * 11
        )
