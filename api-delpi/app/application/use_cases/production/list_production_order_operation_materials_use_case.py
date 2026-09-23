from __future__ import annotations

from app.application.dto.production.list_production_order_operation_materials_request import (
    ListProductionOrderOperationMaterialsRequest,
)
from app.application.use_cases.production.operation_materials_item import (
    normalize_operation_material_item,
)
from app.domain.ports.production.production_orders_repository_port import (
    ProductionOrdersRepositoryPort,
)


class ListProductionOrderOperationMaterialsUseCase:
    """Lista empenhos SD4 ativos da OP+operação — sem fallback SG1."""

    def __init__(self, production_orders_repository: ProductionOrdersRepositoryPort):
        self._production_orders_repository = production_orders_repository

    def execute(self, request: ListProductionOrderOperationMaterialsRequest) -> dict:
        production_order = (request.production_order or "").strip()
        operation = (request.operation or "").strip()
        if not production_order:
            raise ValueError("production_order é obrigatório.")
        if not operation:
            raise ValueError("operation é obrigatório.")

        rows = self._production_orders_repository.fetch_operation_materials(
            production_order=production_order,
            operation=operation,
            branch=request.branch,
        )
        items = [normalize_operation_material_item(row) for row in rows]
        return {
            "branch": request.branch,
            "production_order": production_order,
            "operation": operation,
            "items": items,
            "summary": {
                "material_count": len(items),
                "commitment_count": sum(item["commitment_count"] for item in items),
            },
        }