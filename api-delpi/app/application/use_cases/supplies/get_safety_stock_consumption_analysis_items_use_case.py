from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockConsumptionAnalysisItemsRequest,
)
from app.application.services.supplies.safety_stock_consumption_analysis_query_service import (
    SafetyStockConsumptionAnalysisQueryService,
)
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    ANALYSIS_CALENDAR_DAYS,
)


class GetSafetyStockConsumptionAnalysisItemsUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._query_service = SafetyStockConsumptionAnalysisQueryService(repository)

    def execute(self, request: SafetyStockConsumptionAnalysisItemsRequest) -> dict:
        items, period_start, period_end, period_business_days = (
            self._query_service.load_enriched_items(request)
        )
        sorted_items = self._query_service.sort_items(
            items,
            sort_by=request.sort_by,
            sort_direction=request.sort_direction,
        )
        total = len(sorted_items)
        page_items = sorted_items[request.offset : request.offset + request.page_size]
        total_pages = (total + request.page_size - 1) // request.page_size if total else 0
        return {
            "items": page_items,
            "page": request.page,
            "page_size": request.page_size,
            "total": total,
            "total_pages": total_pages,
            "sort_by": request.sort_by,
            "sort_direction": request.sort_direction,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_calendar_days": ANALYSIS_CALENDAR_DAYS,
            "period_business_days": period_business_days,
        }
