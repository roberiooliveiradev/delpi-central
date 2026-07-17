from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockQueryRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_query_repository import (
    SafetyStockQueryRepository,
)


class GetSafetyStockFiltersUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockQueryRequest) -> dict:
        options = self._repository.fetch_filter_options(
            branch=request.branch,
            include_blocked=request.include_blocked,
        )
        warehouse = SafetyStockQueryRepository.warehouse_metadata()
        wip = warehouse["work_in_process_warehouses"]
        primary = warehouse["primary_warehouse"]
        return {
            "branch": request.branch,
            "product_groups": options.get("product_groups") or [],
            "units": options.get("units") or [],
            "statuses": sorted(
                {
                    "without_safety_stock",
                    "below_safety_stock",
                    "at_safety_stock",
                    "above_safety_stock",
                }
            ),
            "warehouses": [primary, *wip],
            "primary_warehouse": primary,
            "work_in_process_warehouses": wip,
            "work_in_process_note": (
                "Saldo disponível = armazéns 01 + 98 + 99. "
                "Armazéns 50, 98 e 99 também aparecem como estoque em processo."
            ),
        }
