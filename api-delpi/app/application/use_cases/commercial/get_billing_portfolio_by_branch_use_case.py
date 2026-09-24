"""Use case — billing portfolio by branch (forecast × realized)."""

from __future__ import annotations

from typing import Any

from app.application.dto.commercial.billing_portfolio_request import (
    GetBillingPortfolioByBranchRequest,
)
from app.application.use_cases.commercial.billing_portfolio_helpers import (
    contract_meta_from_request,
    fetch_realized_value,
    filters_from_request,
    open_only_from_quantity_basis,
    to_iso_date,
    value_trio,
)
from app.domain.entities.commercial.weekly_portfolio import WeeklyPortfolioBranchTotals
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES


class GetBillingPortfolioByBranchUseCase:
    def __init__(
        self,
        *,
        portfolio_repository: CommercialWeeklyPortfolioRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._portfolio = portfolio_repository
        self._financial = financial_query_repository

    def execute(self, request: GetBillingPortfolioByBranchRequest) -> dict[str, Any]:
        request.validate()
        start_iso = to_iso_date(request.start_date)
        end_iso = to_iso_date(request.end_date)
        assert start_iso and end_iso

        branches = (
            [request.branch]
            if request.branch
            else list(PROTHEUS_BRANCH_CODES)
        )
        forecast_rows = {
            row.branch: row.forecast_value
            for row in self._portfolio.list_delivery_forecast_by_branch(
                start_date=start_iso,
                end_date=end_iso,
                branch=request.branch,
                filters=filters_from_request(request),
                open_only=open_only_from_quantity_basis(request.quantity_basis),
            )
        }
        items: list[WeeklyPortfolioBranchTotals] = []
        for branch_code in branches:
            forecast = round(float(forecast_rows.get(branch_code) or 0), 2)
            realized = fetch_realized_value(
                self._financial,
                start_date=start_iso,
                end_date=end_iso,
                branch=branch_code,
                request=request,
            )
            trio = value_trio(forecast_value=forecast, realized_value=realized)
            items.append(
                WeeklyPortfolioBranchTotals(
                    branch=branch_code,
                    forecast_value=trio.forecast_value,
                    realized_value=trio.realized_value,
                    variance_value=trio.variance_value,
                )
            )

        total_forecast = round(sum(item.forecast_value for item in items), 2)
        total_realized = round(sum(item.realized_value for item in items), 2)
        summary_trio = value_trio(
            forecast_value=total_forecast,
            realized_value=total_realized,
        )

        return {
            "start_date": start_iso,
            "end_date": end_iso,
            **contract_meta_from_request(request).to_dict(),
            "items": [item.to_dict() for item in items],
            "summary": {
                "items_count": len(items),
                **summary_trio.to_dict(),
            },
        }
