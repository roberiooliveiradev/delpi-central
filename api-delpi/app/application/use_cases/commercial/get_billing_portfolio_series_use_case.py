"""Use case — billing portfolio series (forecast × realized by period bucket)."""

from __future__ import annotations

from typing import Any

from app.application.dto.commercial.billing_portfolio_request import (
    GetBillingPortfolioSeriesRequest,
)
from app.application.shared.chart_period_buckets import build_period_buckets
from app.application.use_cases.commercial.billing_portfolio_helpers import (
    contract_meta_from_request,
    fetch_forecast_value,
    fetch_realized_value,
    to_iso_date,
    value_trio,
)
from app.domain.entities.commercial.weekly_portfolio import BillingPortfolioSeriesPoint
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)


class GetBillingPortfolioSeriesUseCase:
    def __init__(
        self,
        *,
        portfolio_repository: CommercialWeeklyPortfolioRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._portfolio = portfolio_repository
        self._financial = financial_query_repository

    def execute(self, request: GetBillingPortfolioSeriesRequest) -> dict[str, Any]:
        request.validate()
        start_iso = to_iso_date(request.start_date)
        end_iso = to_iso_date(request.end_date)
        assert start_iso and end_iso

        buckets_result = build_period_buckets(
            start_date=start_iso,
            end_date=end_iso,
            granularity=request.granularity,
        )
        points: list[BillingPortfolioSeriesPoint] = []
        for bucket in buckets_result.buckets:
            forecast = fetch_forecast_value(
                self._portfolio,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                branch=request.branch,
                request=request,
            )
            realized = fetch_realized_value(
                self._financial,
                start_date=bucket.start_date,
                end_date=bucket.end_date,
                branch=request.branch,
                request=request,
            )
            trio = value_trio(forecast_value=forecast, realized_value=realized)
            points.append(
                BillingPortfolioSeriesPoint(
                    periodo=bucket.label,
                    sort_key=bucket.key,
                    start_date=bucket.start_date,
                    end_date=bucket.end_date,
                    forecast_value=trio.forecast_value,
                    realized_value=trio.realized_value,
                    variance_value=trio.variance_value,
                )
            )

        return {
            "branch": request.branch,
            "start_date": start_iso,
            "end_date": end_iso,
            "granularity": request.granularity,
            "truncated": buckets_result.truncated,
            **contract_meta_from_request(request).to_dict(),
            "points": [point.to_dict() for point in points],
        }
