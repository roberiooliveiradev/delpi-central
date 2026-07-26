"""Histórico de preço unitário do produto com um fornecedor (últimos 12 meses)."""

from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import (
    SafetyStockSupplierPriceHistoryRequest,
)
from app.application.services.product.product_raw_material_price_service import (
    resolve_history_date_range,
)
from app.domain.ports.product.product_raw_material_price_repository_port import (
    ProductRawMaterialPriceRepositoryPort,
)
from app.domain.services.supplies.safety_stock_supplier_price_history_service import (
    map_supplier_price_history_items,
    summarize_supplier_price_history,
)


class GetSafetyStockSupplierPriceHistoryUseCase:
    DEFAULT_HISTORY_LIMIT = 500

    def __init__(self, repository: ProductRawMaterialPriceRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockSupplierPriceHistoryRequest) -> dict:
        date_start, date_end_exclusive = resolve_history_date_range(None, None)
        raw_items = self._repository.fetch_purchase_price_history(
            request.product_code,
            date_start,
            date_end_exclusive,
            branch=request.branch,
            limit=self.DEFAULT_HISTORY_LIMIT,
            supplier_code=request.supplier_code,
            supplier_store=request.supplier_store,
            date_basis="entry",
        )
        items = map_supplier_price_history_items(raw_items)
        return {
            "product_code": request.product_code,
            "branch": request.branch,
            "supplier_code": request.supplier_code,
            "supplier_store": request.supplier_store,
            "start_date": date_start,
            "date_end_exclusive": date_end_exclusive,
            "items": items,
            "total": len(items),
            "summary": summarize_supplier_price_history(items),
        }
