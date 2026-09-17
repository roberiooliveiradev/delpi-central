from __future__ import annotations

from app.application.dto.production.list_production_order_operation_materials_request import (
    ListProductionOrderOperationMaterialsRequest,
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
        items = [_normalize_item(row) for row in rows]
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


def _normalize_item(row: dict) -> dict:
    return {
        "product_code": _text(row.get("product_code")),
        "description": _text(row.get("description")),
        "unit": _text(row.get("unit")),
        "original_qty": _float(row.get("original_qty")),
        "open_qty": _float(row.get("open_qty")),
        "consumed_qty": _float(row.get("consumed_qty")),
        "commitment_count": int(row.get("commitment_count") or 0),
    }


def _text(value: object) -> str:
    return str(value or "").strip()


def _float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
