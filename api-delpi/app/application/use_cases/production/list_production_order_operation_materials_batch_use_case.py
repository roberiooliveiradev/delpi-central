from __future__ import annotations

from app.application.dto.production.list_production_order_operation_materials_batch_request import (
    ListProductionOrderOperationMaterialsBatchRequest,
)
from app.application.use_cases.production.operation_materials_item import (
    normalize_operation_material_item,
    text,
)
from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)


class ListProductionOrderOperationMaterialsBatchUseCase:
    """Lista empenhos SD4 ativos de várias OPs de uma vez — sem fallback SG1."""

    def __init__(self, production_orders_repository: ProductionOrdersRepositoryPort):
        self._production_orders_repository = production_orders_repository

    def execute(
        self, request: ListProductionOrderOperationMaterialsBatchRequest
    ) -> dict:
        orders = tuple(request.production_orders)

        rows: list[dict] = []
        if orders:
            rows = self._production_orders_repository.fetch_operation_materials_batch(
                production_orders=orders,
                branch=request.branch,
            )

        items = [_normalize_batch_item(row) for row in rows]
        return {
            "branch": request.branch,
            "production_orders": list(orders),
            "items": items,
            "summary": {
                "requested_count": len(orders),
                "returned_count": len(items),
                "order_count": len({item["production_order"] for item in items}),
                "commitment_count": sum(item["commitment_count"] for item in items),
            },
        }


def _normalize_batch_item(row: dict) -> dict:
    item = {
        "production_order": text(row.get("production_order")),
        "operation": text(row.get("operation")),
    }
    item.update(normalize_operation_material_item(row))
    return item
