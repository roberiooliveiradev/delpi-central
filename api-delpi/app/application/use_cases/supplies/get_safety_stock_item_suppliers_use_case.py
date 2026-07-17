"""Fornecedores vinculados ao produto com última compra (SA5 × SA2 × SD1)."""

from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockItemDetailsRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    build_collection_block,
)


class GetSafetyStockItemSuppliersUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockItemDetailsRequest) -> dict:
        suppliers = self._repository.fetch_linked_suppliers(
            branch=request.branch,
            product_code=request.product_code,
        )
        return build_collection_block(suppliers)
