"""Composer for the R03/P7 stock-inventory snapshot query (doc 49).

The dataset-scope resolver is the fail-closed gate for the shared Protheus
dataset — wired to ``FINANCEIRO_STOCK_INVENTORY_ENABLED`` (default off).
"""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    SharedDatasetStockInventoryScopeResolver,
    StockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_stock_inventory.export_stock_inventory_use_case import (
    ExportStockInventoryUseCase,
)
from app.application.use_cases.financeiro_stock_inventory.get_stock_inventory_use_case import (
    GetStockInventoryUseCase,
)
from app.config import settings
from app.infrastructure.persistence.totvs.financeiro_stock_inventory.stock_inventory_repository import (
    StockInventoryRepository,
)


def get_stock_inventory_scope_resolver() -> StockInventoryScopeResolver:
    return SharedDatasetStockInventoryScopeResolver(
        enabled=settings.FINANCEIRO_STOCK_INVENTORY_ENABLED
    )


def build_stock_inventory_use_case() -> GetStockInventoryUseCase:
    return GetStockInventoryUseCase(
        repository=StockInventoryRepository(),
        scope_resolver=get_stock_inventory_scope_resolver(),
    )


def build_export_stock_inventory_use_case() -> ExportStockInventoryUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportStockInventoryUseCase(
        get_use_case=build_stock_inventory_use_case()
    )
