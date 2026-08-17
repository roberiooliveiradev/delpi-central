"""BFF OTD panel — encaminha page/sort/status/search para api-delpi."""

from __future__ import annotations

import inspect

from commercial_app.interface.http.routes import analytics_routes


def test_bff_otd_panel_accepts_list_query_params() -> None:
    names = set(inspect.signature(analytics_routes.bff_otd_panel).parameters)
    for required in ("status", "page", "page_size", "sort_by", "sort_dir", "search"):
        assert required in names


def test_common_filters_includes_otd_list_keys() -> None:
    params = analytics_routes._common_filters(
        start_date="2026-08-01",
        end_date="2026-08-13",
        branch="02",
        customer_segment=None,
        status="late",
        page=2,
        page_size=30,
        sort_by="days_diff",
        sort_dir="desc",
        search="WEG",
    )
    assert params["status"] == "late"
    assert params["page"] == 2
    assert params["page_size"] == 30
    assert params["sort_by"] == "days_diff"
    assert params["sort_dir"] == "desc"
    assert params["search"] == "WEG"


def test_bff_list_proposals_accepts_product_filters() -> None:
    names = set(inspect.signature(analytics_routes.bff_list_proposals).parameters)
    assert "product_code" in names
    assert "product_group" in names


def test_common_filters_includes_product_keys() -> None:
    params = analytics_routes._common_filters(
        start_date="2026-08-01",
        end_date="2026-08-13",
        branch="01",
        customer_segment=None,
        product_code="90AAAA01",
        product_group="1234",
    )
    assert params["product_code"] == "90AAAA01"
    assert params["product_group"] == "1234"
