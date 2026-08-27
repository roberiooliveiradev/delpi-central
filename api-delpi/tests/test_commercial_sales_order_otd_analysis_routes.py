"""Smoke + unit — get_commercial_sales_order_otd_analysis."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch(f"{_COMMERCIAL}.build_get_commercial_sales_order_otd_analysis_use_case")
def test_get_commercial_sales_order_otd_analysis_returns_meta(
    mock_build, _mock_enrich
) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "start_date": "2026-08-03",
            "end_date": "2026-08-28",
            "branch": "01",
            "customer_segment": "weg",
            "totals": {"otd_pct": 93.4, "total_qty": 100.0},
            "by_branch": {"branch_01": {"otd_pct": 93.4, "total_qty": 100.0}},
        },
        "series": [],
        "by_customer": [],
        "granularity": "week",
        "group_by": "customer",
        "pagination": {"page": 1, "page_size": 50, "total": 0, "has_more": False},
    }
    mock_build.return_value = use_case

    response = router_mod.get_commercial_sales_order_otd_analysis(
        start_date="2026-08-03",
        end_date="2026-08-28",
        granularity="week",
        branch="01",
        customer_segment="weg",
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        group_by="customer",
        page=1,
        page_size=50,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_sales_order_otd_analysis",
        shape="composite_analysis",
    )
    assert payload["data"]["summary"]["totals"]["otd_pct"] == 93.4


def test_otd_analysis_use_case_builds_series_and_pagination():
    from app.application.use_cases.commercial.get_commercial_sales_order_otd_analysis_use_case import (
        GetCommercialSalesOrderOtdAnalysisUseCase,
    )
    from app.domain.services.commercial_analysis_filter_request import (
        CommercialAnalysisFilterRequest,
    )

    repo = MagicMock()
    repo.get_sales_order_otd_analysis_summary.return_value = {
        "total_lines": 10,
        "total_qty": 100.0,
        "fulfilled_qty": 90.0,
        "on_time_lines": 9,
        "late_lines": 1,
        "fulfillment_pct": 90.0,
        "otd_pct": 90.0,
    }
    repo.list_sales_order_otd_analysis_by_customer.return_value = [
        {
            "customer_code": "0001",
            "customer_store": "01",
            "customer_name": "Weg Motores",
            "branch": "01",
            "total_lines": 5,
            "total_qty": 50.0,
            "fulfilled_qty": 50.0,
            "on_time_lines": 5,
            "late_lines": 0,
            "fulfillment_pct": 100.0,
            "otd_pct": 100.0,
        }
    ]

    uc = GetCommercialSalesOrderOtdAnalysisUseCase(sales_order_otd_repository=repo)
    result = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20260803",
            end_date="20260807",
            granularity="week",
            branch="01",
            group_by="customer",
            page=1,
            page_size=50,
        )
    )
    assert result["summary"]["totals"]["otd_pct"] == 90.0
    assert len(result["by_customer"]) == 1
    assert result["pagination"]["total"] == 1
    assert len(result["series"]) >= 1
