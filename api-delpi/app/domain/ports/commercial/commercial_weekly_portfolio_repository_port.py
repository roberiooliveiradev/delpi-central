from __future__ import annotations

from typing import Optional, Protocol

from app.domain.entities.commercial.weekly_portfolio import (
    WeeklyPortfolioBranchForecast,
    WeeklyPortfolioCustomerForecast,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)


class CommercialWeeklyPortfolioRepositoryPort(Protocol):
    def list_delivery_week_forecast_by_customer(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: Optional[str],
        filters: CommercialAnalysisFilterRequest,
        open_only: bool = False,
    ) -> list[WeeklyPortfolioCustomerForecast]:
        ...

    def sum_delivery_forecast(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: Optional[str],
        filters: CommercialAnalysisFilterRequest,
        open_only: bool = False,
    ) -> float:
        ...

    def list_delivery_forecast_by_branch(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: Optional[str],
        filters: CommercialAnalysisFilterRequest,
        open_only: bool = False,
    ) -> list[WeeklyPortfolioBranchForecast]:
        ...
