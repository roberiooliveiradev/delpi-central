from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockItemDetailsRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    SafetyStockConsumptionAnalysisService,
)


class GetSafetyStockConsumptionAnalysisItemDetailsUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockItemDetailsRequest) -> dict | None:
        period_start, period_end, period_business_days = (
            SafetyStockConsumptionAnalysisService.resolve_period()
        )
        annual_start, annual_end, year_list = (
            SafetyStockConsumptionAnalysisService.resolve_annual_comparison_period(
                as_of=period_end
            )
        )
        rows = self._repository.fetch_consumption_analysis_rows(
            branch=request.branch,
            period_start=period_start.strftime("%Y%m%d"),
            include_blocked=True,
            product_group=None,
            unit=None,
            search=None,
            product_code=request.product_code,
        )
        if not rows:
            return None

        item = SafetyStockConsumptionAnalysisService.enrich_row(
            rows[0],
            period_start=period_start,
            period_end=period_end,
            period_business_days=period_business_days,
            as_of=period_end,
        )
        monthly_all = self._repository.fetch_consumption_monthly_series(
            branch=request.branch,
            product_code=request.product_code,
            period_start=annual_start.strftime("%Y%m%d"),
        )
        monthly = SafetyStockConsumptionAnalysisService.filter_monthly_series_for_period(
            monthly_all,
            period_start=period_start,
            period_end=period_end,
        )
        annual_comparison = SafetyStockConsumptionAnalysisService.build_annual_comparison(
            monthly_all,
            years=year_list,
            period_start=annual_start,
            period_end=annual_end,
        )
        return {
            "item": item,
            "monthly_consumption": {
                "items": monthly,
                "total": len(monthly),
            },
            "annual_comparison": annual_comparison,
            "calculation_memory": (
                SafetyStockConsumptionAnalysisService.build_calculation_memory(item)
            ),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }
