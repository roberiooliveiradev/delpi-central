"""Regressão — group_by customer/branch/none nas rotas consolidadas comerciais."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.commercial.commercial_rol_series_response import (
    CommercialRolSeriesPointDto,
    CommercialRolSeriesResponse,
)
from app.application.use_cases.commercial.commercial_analysis_payload_helpers import (
    branch_breakdown_rows,
)
from app.application.use_cases.commercial.get_commercial_rol_analysis_use_case import (
    GetCommercialRolAnalysisUseCase,
)
from app.application.use_cases.commercial.get_commercial_sales_order_otd_analysis_use_case import (
    GetCommercialSalesOrderOtdAnalysisUseCase,
)
from app.domain.entities.commercial.rol_by_customer import RolByCustomerItem, RolByCustomerResult
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)


def _rol_metrics() -> dict[str, float]:
    return {
        "rol": 100.0,
        "gross_revenue": 120.0,
        "returns": 5.0,
        "discounts": 3.0,
    }


def _build_rol_use_case(*, by_customer_items: tuple[RolByCustomerItem, ...] = ()) -> GetCommercialRolAnalysisUseCase:
    financial = MagicMock()
    financial.get_rol.return_value = _rol_metrics()
    series_uc = MagicMock()
    series_uc.execute.return_value = CommercialRolSeriesResponse(
        granularity="week",
        truncated=False,
        points=[
            CommercialRolSeriesPointDto(
                periodo="01/08/24 – 07/08/24",
                sort_key="2024-08-01",
                start_date="2024-08-01",
                end_date="2024-08-07",
                rol_matrix=50.0,
                rol_branch=70.0,
            )
        ],
    )
    by_customer_uc = MagicMock()
    by_customer_uc.execute.return_value = RolByCustomerResult(
        branch="consolidated",
        start_date="2024-08-01",
        end_date="2024-08-31",
        items=by_customer_items,
        others=None,
        total_rol=sum(item.rol for item in by_customer_items),
        customers_count=len(by_customer_items),
    )
    portfolio_repo = MagicMock()
    portfolio_repo.list_delivery_week_forecast_by_customer.return_value = []
    return GetCommercialRolAnalysisUseCase(
        financial_query_repository=financial,
        rol_series_use_case=series_uc,
        rol_by_customer_use_case=by_customer_uc,
        weekly_portfolio_repository=portfolio_repo,
    )


def test_rol_group_by_customer_populates_by_customer():
    items = (
        RolByCustomerItem(
            customer_code="0001",
            customer_store="01",
            customer_name="Cliente A",
            rol=10.0,
            share_pct=50.0,
            rank=1,
        ),
    )
    uc = _build_rol_use_case(by_customer_items=items)
    result = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20240801",
            end_date="20240831",
            group_by="customer",
        )
    )
    assert len(result["by_customer"]) == 1
    assert result["by_customer"][0]["customer_name"] == "Cliente A"
    assert result["pagination"]["total"] == 1
    assert "by_branch" not in result
    assert len(result["series"]) == 1


def test_rol_group_by_branch_exposes_tabular_by_branch():
    uc = _build_rol_use_case()
    result = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20240801",
            end_date="20240831",
            group_by="branch",
        )
    )
    assert result["by_customer"] == []
    assert result.get("pagination") is None
    assert len(result["by_branch"]) == 2
    branches = {row["branch"] for row in result["by_branch"]}
    assert branches == {"01", "02"}
    assert result["by_branch"][0]["rol"] == 100.0


def test_rol_group_by_none_skips_customer_breakdown():
    uc = _build_rol_use_case(
        by_customer_items=(
            RolByCustomerItem(
                customer_code="0001",
                customer_store="01",
                customer_name="Cliente A",
                rol=10.0,
                share_pct=100.0,
                rank=1,
            ),
        )
    )
    result = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20240801",
            end_date="20240831",
            group_by="none",
        )
    )
    assert result["by_customer"] == []
    assert result.get("pagination") is None
    assert len(result["series"]) == 1
    assert result["series"][0]["rol_filial_01"] == 50.0


def test_branch_breakdown_rows_normalizes_branch_codes():
    rows = branch_breakdown_rows(
        {
            "branch_01": {"rol": 1.0},
            "branch_02": {"rol": 2.0},
        }
    )
    assert rows == [
        {"branch": "01", "rol": 1.0},
        {"branch": "02", "rol": 2.0},
    ]


def test_otd_group_by_customer_and_branch():
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

    by_customer = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20260803",
            end_date="20260807",
            group_by="customer",
        )
    )
    assert len(by_customer["by_customer"]) == 1
    assert by_customer["summary"]["totals"]["otd_pct"] == 90.0
    assert "by_branch" in by_customer["summary"]

    by_branch = uc.execute(
        CommercialAnalysisFilterRequest(
            start_date="20260803",
            end_date="20260807",
            group_by="branch",
        )
    )
    assert by_branch["by_customer"] == []
    assert len(by_branch["by_branch"]) == 2
    assert {row["branch"] for row in by_branch["by_branch"]} == {"01", "02"}
