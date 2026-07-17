from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockItemsRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)


class GetSafetyStockItemsUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockItemsRequest) -> dict:
        total = self._repository.count_items(
            branch=request.branch,
            include_blocked=request.include_blocked,
            product_group=request.product_group,
            unit=request.unit,
            search=request.search,
            status=request.status,
            include_without_safety_stock=request.include_without_safety_stock,
        )
        items = self._repository.fetch_items(
            branch=request.branch,
            include_blocked=request.include_blocked,
            product_group=request.product_group,
            unit=request.unit,
            search=request.search,
            status=request.status,
            include_without_safety_stock=request.include_without_safety_stock,
            sort_by=request.sort_by,
            sort_direction=request.sort_direction,
            offset=request.offset,
            page_size=request.page_size,
        )
        total_pages = (total + request.page_size - 1) // request.page_size if total else 0
        return {
            "items": items,
            "page": request.page,
            "page_size": request.page_size,
            "total": total,
            "total_pages": total_pages,
            "sort_by": request.sort_by,
            "sort_direction": request.sort_direction,
        }
