"""Smoke — get_commercial_rol envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.enrich_dashboard_metric", side_effect=lambda payload, **_: payload)
@patch(f"{_COMMERCIAL}.build_get_commercial_rol_analysis_use_case")
def test_get_commercial_rol_returns_meta(mock_build, _mock_enrich) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "summary": {
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "branch": None,
            "customer_segment": None,
            "totals": {"rol_with_ipi": 0.0},
            "by_branch": {},
        },
        "series": [],
        "by_customer": [],
        "granularity": "week",
        "group_by": "customer",
        "pagination": {"page": 1, "page_size": 50, "total": 0, "has_more": False},
    }
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol(
        start_date="2026-08-01",
        end_date="2026-08-31",
        granularity="week",
        branch=None,
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        group_by="customer",
        page=1,
        page_size=50,
        include=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol",
        shape="composite_analysis",
    )
    assert payload["data"]["summary"]["totals"]["rol_with_ipi"] == 0.0


def test_get_commercial_rol_analysis_use_case_builds_payload():
    from app.application.use_cases.commercial.get_commercial_rol_analysis_use_case import (
        GetCommercialRolAnalysisUseCase,
    )
    from app.application.dto.commercial.commercial_rol_series_response import (
        CommercialRolSeriesPointDto,
        CommercialRolSeriesResponse,
    )
    from app.domain.entities.commercial.rol_by_customer import RolByCustomerResult
    from app.domain.services.commercial_analysis_filter_request import (
        CommercialAnalysisFilterRequest,
    )

    financial = MagicMock()
    financial.get_rol.return_value = {
        "rol": 10.0,
        "rol_with_ipi": 12.0,
        "gross_revenue": 20.0,
        "returns": 1.0,
        "discounts": 2.0,
    }
    series_uc = MagicMock()
    series_uc.execute.return_value = CommercialRolSeriesResponse(
        granularity="week",
        truncated=False,
        points=[
            CommercialRolSeriesPointDto(
                periodo="01/08/26 – 07/08/26",
                sort_key="2026-08-01",
                start_date="2026-08-01",
                end_date="2026-08-07",
                rol_matrix=5.0,
                rol_branch=7.0,
            )
        ],
    )
    by_customer_uc = MagicMock()
    by_customer_uc.execute.return_value = RolByCustomerResult(
        branch="consolidated",
        start_date="2026-08-01",
        end_date="2026-08-31",
        items=(),
        others=None,
        total_rol=0.0,
        customers_count=0,
    )
    portfolio_repo = MagicMock()
    portfolio_repo.list_delivery_week_forecast_by_customer.return_value = []

    uc = GetCommercialRolAnalysisUseCase(
        financial_query_repository=financial,
        rol_series_use_case=series_uc,
        rol_by_customer_use_case=by_customer_uc,
        weekly_portfolio_repository=portfolio_repo,
    )
    result = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20260801",
            end_date="20260831",
            granularity="week",
            group_by="customer",
        )
    )
    assert result["summary"]["totals"]["rol_with_ipi"] == 24.0
    assert len(result["series"]) == 1
    assert result["series"][0]["branch_01"]["rol_with_ipi"] == 5.0
    assert "pagination" in result
