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


class ListInventoryAdjustmentsUseCase:
    def __init__(self, repository: InventoryAdjustmentsRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: InventoryAdjustmentsRequest) -> dict:
        start, end, end_exclusive = resolve_required_period(request)
        page = max(int(request.page or 1), 1)
        page_size = min(max(int(request.page_size or 50), 1), 500)
        result = self._repository.fetch_adjustment_items(
            date_start=start,
            date_end_exclusive=end_exclusive,
            branch=request.branch,
            product_code=request.product_code,
            warehouse=request.warehouse,
            nature=request.nature,
            page=page,
            page_size=page_size,
        )
        total = int(result.get("total") or 0)
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return {
            "period_start": ResponseDateFormatService.format_date(start),
            "period_end": ResponseDateFormatService.format_date(end),
            "items": ResponseDateFormatService.format_items(
                result.get("items") or []
            ),
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
