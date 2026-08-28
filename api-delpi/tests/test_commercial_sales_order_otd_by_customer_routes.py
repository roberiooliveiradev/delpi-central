"""Smoke — get_sales_order_otd_by_customer / by-branch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch(f"{_COMMERCIAL}.build_get_sales_order_otd_use_case")
def test_get_sales_order_otd_summary_returns_meta(mock_build, _mock_enrich) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "start_date": "2026-08-01",
        "end_date": "2026-08-28",
        "total_lines": 10,
        "on_time_lines": 9,
        "late_lines": 1,
        "sales_order_otd_pct": 90.0,
    }
    mock_build.return_value = use_case

    response = router_mod.get_sales_order_otd_summary(
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-28",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_sales_order_otd_summary",
        shape="scalar",
        entity="sales_order_otd_summary",
    )
    assert payload["data"]["sales_order_otd_pct"] == 90.0


@patch(f"{_COMMERCIAL}.build_get_sales_order_otd_by_customer_use_case")
def test_get_sales_order_otd_by_customer_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "branch": None,
        "items": [
            {
                "customer_code": "0001",
                "customer_store": "01",
                "customer_name": "Cliente A",
                "branch": "01",
                "total_lines": 2,
                "total_qty": 10.0,
                "fulfilled_qty": 8.0,
                "on_time_lines": 1,
                "late_lines": 1,
                "fulfillment_pct": 80.0,
                "otd_pct": 50.0,
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "has_more": False},
        "summary": {"items_count": 1, "customers_count": 1},
    }
    mock_build.return_value = use_case

    response = router_mod.get_sales_order_otd_by_customer(
        branch=None,
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        page=1,
        page_size=50,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_sales_order_otd_by_customer",
        shape="paged_list",
    )
    assert payload["data"]["items"][0]["otd_pct"] == 50.0


@patch(f"{_COMMERCIAL}.build_get_sales_order_otd_by_branch_use_case")
def test_get_sales_order_otd_by_branch_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "items": [
            {
                "branch": "01",
                "total_lines": 10,
                "total_qty": 100.0,
                "fulfilled_qty": 90.0,
                "on_time_lines": 8,
                "late_lines": 2,
                "fulfillment_pct": 90.0,
                "otd_pct": 80.0,
            },
            {
                "branch": "02",
                "total_lines": 5,
                "total_qty": 50.0,
                "fulfilled_qty": 40.0,
                "on_time_lines": 4,
                "late_lines": 1,
                "fulfillment_pct": 80.0,
                "otd_pct": 80.0,
            },
        ],
        "summary": {"items_count": 2},
    }
    mock_build.return_value = use_case

    response = router_mod.get_sales_order_otd_by_branch(
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_sales_order_otd_by_branch",
        shape="paged_list",
    )
    assert [row["branch"] for row in payload["data"]["items"]] == ["01", "02"]


@patch(f"{_COMMERCIAL}.build_get_sales_order_otd_series_by_customer_use_case")
def test_get_sales_order_otd_series_by_customer_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-08-03",
        "end_date": "2026-08-16",
        "branch": None,
        "granularity": "week",
        "truncated": False,
        "items": [
            {
                "customer_code": "0001",
                "customer_store": "01",
                "customer_name": "Cliente A",
                "branch": "01",
                "periodo": "03/08/26 – 09/08/26",
                "sort_key": "2026-W32",
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
                "total_lines": 2,
                "total_qty": 10.0,
                "fulfilled_qty": 8.0,
                "on_time_lines": 1,
                "late_lines": 1,
                "fulfillment_pct": 80.0,
                "otd_pct": 50.0,
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "has_more": False},
        "summary": {
            "granularity": "week",
            "truncated": False,
            "customers_count": 1,
            "buckets_count": 2,
            "items_count": 1,
        },
    }
    mock_build.return_value = use_case

    response = router_mod.get_sales_order_otd_series_by_customer(
        granularity="week",
        start_date="2026-08-03",
        end_date="2026-08-16",
        branch=None,
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        page=1,
        page_size=50,
        top_customers=20,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_sales_order_otd_series_by_customer",
        shape="paged_list",
    )
    assert payload["data"]["items"][0]["periodo"]
    assert payload["data"]["items"][0]["otd_pct"] == 50.0
