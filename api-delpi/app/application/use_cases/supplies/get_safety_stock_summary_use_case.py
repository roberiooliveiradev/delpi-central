from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockQueryRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)


class GetSafetyStockSummaryUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockQueryRequest) -> dict:
        return self._repository.fetch_summary(
            branch=request.branch,
            include_blocked=request.include_blocked,
            product_group=request.product_group,
            unit=request.unit,
            search=request.search,
            status=request.status,
            include_without_safety_stock=request.include_without_safety_stock,
        )
