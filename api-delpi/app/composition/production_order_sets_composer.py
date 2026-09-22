"""Composition — conjuntos de ordens de produção."""

from __future__ import annotations

from app.application.use_cases.production.get_production_order_sets_use_cases import (
    GetProductionOrderSetsIncompleteUseCase,
    GetProductionOrderSetsQuantityMismatchesUseCase,
)
from app.infrastructure.persistence.totvs.production.production_order_sets_repository import (
    ProductionOrderSetsRepository,
)


def build_get_production_order_sets_incomplete_use_case() -> (
    GetProductionOrderSetsIncompleteUseCase
):
    return GetProductionOrderSetsIncompleteUseCase(
        repository=ProductionOrderSetsRepository()
    )


def build_get_production_order_sets_quantity_mismatches_use_case() -> (
    GetProductionOrderSetsQuantityMismatchesUseCase
):
    return GetProductionOrderSetsQuantityMismatchesUseCase(
        repository=ProductionOrderSetsRepository()
    )
