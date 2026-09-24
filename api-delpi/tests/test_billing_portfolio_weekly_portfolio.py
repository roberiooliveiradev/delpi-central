"""Unit tests — billing portfolio / weekly portfolio SQL predicates and use cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.commercial.billing_portfolio_request import (
    GetBillingPortfolioByBranchRequest,
    GetBillingPortfolioByCustomerRequest,
    GetBillingPortfolioSeriesRequest,
    GetBillingPortfolioSummaryRequest,
)
from app.application.use_cases.commercial.get_billing_portfolio_by_branch_use_case import (
    GetBillingPortfolioByBranchUseCase,
)
from app.application.use_cases.commercial.get_billing_portfolio_by_customer_use_case import (
    GetBillingPortfolioByCustomerUseCase,
)
from app.application.use_cases.commercial.get_billing_portfolio_series_use_case import (
    GetBillingPortfolioSeriesUseCase,
)
from app.application.use_cases.commercial.get_billing_portfolio_summary_use_case import (
    GetBillingPortfolioSummaryUseCase,
)
from app.domain.entities.commercial.rol_by_customer import (
    RolByCustomerItem,
    RolByCustomerResult,
)
from app.domain.entities.commercial.weekly_portfolio import (
    BillingPortfolioValueTrio,
    WeeklyPortfolioBranchForecast,
    WeeklyPortfolioCustomerForecast,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_weekly_portfolio_repository import (
    CommercialWeeklyPortfolioRepository,
)


def test_billing_portfolio_value_trio_variance() -> None:
    trio = BillingPortfolioValueTrio.from_parts(
        forecast_value=100.0,
        realized_value=80.0,
    )
    assert trio.variance_value == -20.0
    assert trio.to_dict()["forecast_value"] == 100.0


def test_weekly_portfolio_forecast_where_planned_and_open() -> None:
    filters = CommercialAnalysisFilterRequest(customer_segment="new_business")
    where_planned, _, qty_planned = CommercialWeeklyPortfolioRepository._build_forecast_where(
        start_date="2026-08-10",
        end_date="2026-08-16",
        branch="02",
        filters=filters,
        open_only=False,
    )
    where_open, _, qty_open = CommercialWeeklyPortfolioRepository._build_forecast_where(
        start_date="2026-08-10",
        end_date="2026-08-16",
        branch="02",
        filters=filters,
        open_only=True,
    )
    assert "C6.C6_ENTREG" in where_planned
    assert "C6.C6_FILIAL" in where_planned
    assert "C6.C6_QTDVEN" == qty_planned or qty_planned == "C6.C6_QTDVEN"
    assert "(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0))" in qty_open
    assert "(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0)) > 0" in where_open
    assert "(C6.C6_QTDVEN - ISNULL(C6.C6_QTDENT, 0)) > 0" not in where_planned


def test_get_billing_portfolio_summary_positive_new_business() -> None:
    portfolio = MagicMock()
    portfolio.sum_delivery_forecast.return_value = 66571.05
    portfolio.list_delivery_forecast_by_branch.return_value = [
        WeeklyPortfolioBranchForecast(branch="02", forecast_value=66571.05),
    ]
    financial = MagicMock()
    financial.get_rol.return_value = {"rol": 50000.0, "gross_revenue": 60000.0}

    result = GetBillingPortfolioSummaryUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioSummaryRequest(
            start_date="2026-08-10",
            end_date="2026-08-16",
            branch="02",
            customer_segment="new_business",
            nature="order_gross",
            quantity_basis="planned",
        )
    )
    assert result["forecast_value"] == 66571.05
    assert result["realized_value"] == 60000.0
    assert result["variance_value"] == round(60000.0 - 66571.05, 2)
    assert result["nature"] == "order_gross"
    assert result["quantity_basis"] == "planned"
    assert result["forecast_date_basis"] == "C6_ENTREG"
    assert result["realized_date_basis"] == "D2_EMISSAO"
    assert result["as_of"] == "live"
    assert result["by_branch"][0]["branch"] == "02"


def test_get_billing_portfolio_summary_sibling_weg_rol_nature() -> None:
    portfolio = MagicMock()
    portfolio.sum_delivery_forecast.return_value = 1000.0
    portfolio.list_delivery_forecast_by_branch.return_value = [
        WeeklyPortfolioBranchForecast(branch="01", forecast_value=1000.0),
    ]
    financial = MagicMock()
    financial.get_rol.return_value = {"rol": 900.0, "gross_revenue": 1100.0}

    result = GetBillingPortfolioSummaryUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioSummaryRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            branch="01",
            customer_segment="weg",
            nature="rol",
            quantity_basis="planned",
        )
    )
    assert result["realized_value"] == 900.0
    assert result["nature"] == "rol"


def test_get_billing_portfolio_summary_negative_empty_period() -> None:
    portfolio = MagicMock()
    portfolio.sum_delivery_forecast.return_value = 0.0
    portfolio.list_delivery_forecast_by_branch.return_value = []
    financial = MagicMock()
    financial.get_rol.return_value = {"rol": 0.0, "gross_revenue": 0.0}

    result = GetBillingPortfolioSummaryUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioSummaryRequest(
            start_date="2099-01-01",
            end_date="2099-01-07",
            nature="order_gross",
        )
    )
    assert result["forecast_value"] == 0.0
    assert result["realized_value"] == 0.0
    assert result["variance_value"] == 0.0
    assert [row["branch"] for row in result["by_branch"]] == ["01", "02"]


def test_get_billing_portfolio_series_week_and_day() -> None:
    portfolio = MagicMock()
    portfolio.sum_delivery_forecast.return_value = 10.0
    financial = MagicMock()
    financial.get_rol.return_value = {"rol": 5.0, "gross_revenue": 8.0}

    week = GetBillingPortfolioSeriesUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioSeriesRequest(
            start_date="2026-08-10",
            end_date="2026-08-16",
            granularity="week",
        )
    )
    assert week["granularity"] == "week"
    assert week["truncated"] is False
    assert len(week["points"]) >= 1
    assert "forecast_value" in week["points"][0]
    assert "realized_value" in week["points"][0]
    assert "variance_value" in week["points"][0]

    day = GetBillingPortfolioSeriesUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioSeriesRequest(
            start_date="2026-08-10",
            end_date="2026-08-12",
            granularity="day",
        )
    )
    assert day["granularity"] == "day"
    assert len(day["points"]) == 3


def test_get_billing_portfolio_by_customer_merge_and_exclude() -> None:
    portfolio = MagicMock()
    portfolio.list_delivery_week_forecast_by_customer.return_value = [
        WeeklyPortfolioCustomerForecast(
            customer_code="000223",
            customer_name="Wanke",
            branch="02",
            forecast_value=66571.05,
        ),
        WeeklyPortfolioCustomerForecast(
            customer_code="000099",
            customer_name="Excluded",
            branch="02",
            forecast_value=100.0,
        ),
    ]
    rol_repo = MagicMock()
    rol_repo.get_rol_by_customer.return_value = RolByCustomerResult(
        branch="02",
        start_date="2026-08-10",
        end_date="2026-08-16",
        items=(
            RolByCustomerItem(
                customer_code="000223",
                customer_store="01",
                customer_name="Wanke",
                rol=50000.0,
                share_pct=100.0,
                rank=1,
                gross_revenue=55000.0,
            ),
        ),
        others=None,
        total_rol=50000.0,
        customers_count=1,
    )

    result = GetBillingPortfolioByCustomerUseCase(
        portfolio_repository=portfolio,
        rol_by_customer_repository=rol_repo,
    ).execute(
        GetBillingPortfolioByCustomerRequest(
            start_date="2026-08-10",
            end_date="2026-08-16",
            branch="02",
            exclude_customer_codes=["000099"],
            nature="order_gross",
            page=1,
            page_size=50,
        )
    )
    # UC merges whatever the repos return; exclude is applied by repos via filters.
    codes = {item["customer_code"] for item in result["items"]}
    assert "000223" in codes
    wanke = next(item for item in result["items"] if item["customer_code"] == "000223")
    assert wanke["forecast_value"] == 66571.05
    assert wanke["realized_value"] == 55000.0
    assert "variance_value" in wanke
    assert result["summary"]["forecast_value"] > 0


def test_get_billing_portfolio_by_customer_empty() -> None:
    portfolio = MagicMock()
    portfolio.list_delivery_week_forecast_by_customer.return_value = []
    rol_repo = MagicMock()
    rol_repo.get_rol_by_customer.return_value = RolByCustomerResult(
        branch="consolidated",
        start_date="2099-01-01",
        end_date="2099-01-07",
        items=(),
        others=None,
        total_rol=0.0,
        customers_count=0,
    )
    result = GetBillingPortfolioByCustomerUseCase(
        portfolio_repository=portfolio,
        rol_by_customer_repository=rol_repo,
    ).execute(
        GetBillingPortfolioByCustomerRequest(
            start_date="2099-01-01",
            end_date="2099-01-07",
        )
    )
    assert result["items"] == []
    assert result["summary"]["customers_count"] == 0


def test_get_billing_portfolio_by_branch_consolidated_and_filtered() -> None:
    portfolio = MagicMock()
    portfolio.list_delivery_forecast_by_branch.return_value = [
        WeeklyPortfolioBranchForecast(branch="01", forecast_value=100.0),
        WeeklyPortfolioBranchForecast(branch="02", forecast_value=50.0),
    ]
    financial = MagicMock()
    financial.get_rol.side_effect = [
        {"rol": 80.0, "gross_revenue": 90.0},
        {"rol": 40.0, "gross_revenue": 45.0},
    ]
    consolidated = GetBillingPortfolioByBranchUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioByBranchRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            nature="order_gross",
        )
    )
    assert [row["branch"] for row in consolidated["items"]] == ["01", "02"]
    assert consolidated["summary"]["forecast_value"] == 150.0

    portfolio.list_delivery_forecast_by_branch.return_value = [
        WeeklyPortfolioBranchForecast(branch="01", forecast_value=100.0),
    ]
    financial.get_rol.side_effect = [{"rol": 80.0, "gross_revenue": 90.0}]
    only_01 = GetBillingPortfolioByBranchUseCase(
        portfolio_repository=portfolio,
        financial_query_repository=financial,
    ).execute(
        GetBillingPortfolioByBranchRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
            branch="01",
            nature="order_gross",
        )
    )
    assert [row["branch"] for row in only_01["items"]] == ["01"]


def test_billing_portfolio_request_rejects_invalid_nature() -> None:
    with pytest.raises(ValueError, match="nature"):
        GetBillingPortfolioSummaryRequest(
            start_date="2026-08-01",
            end_date="2026-08-07",
            nature="invalid",
        ).validate()
