from __future__ import annotations

from app.application.dto.supplies.inventory_adjustments_request import (
    InventoryAdjustmentsRequest,
)
from app.application.services.response_date_format_service import (
    ResponseDateFormatService,
)
from app.application.use_cases.supplies.inventory_adjustments_shared import (
    resolve_required_period,
)
from app.domain.ports.supplies.inventory_adjustments_repository_port import (
    InventoryAdjustmentsRepositoryPort,
)


class GetInventoryAdjustmentsSummaryUseCase:
    def __init__(self, repository: InventoryAdjustmentsRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: InventoryAdjustmentsRequest) -> dict:
        start, end, end_exclusive = resolve_required_period(request)
        payload = self._repository.fetch_adjustment_summary(
            date_start=start,
            date_end_exclusive=end_exclusive,
            branch=request.branch,
            product_code=request.product_code,
            warehouse=request.warehouse,
            nature=request.nature,
        )
        return {
            "period_start": ResponseDateFormatService.format_date(start),
            "period_end": ResponseDateFormatService.format_date(end),
            **payload,
        }
