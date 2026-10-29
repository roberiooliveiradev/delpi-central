"""Composer for the R05 stock-movements summary (MATR320, doc 85 §5).

The dataset-scope resolver is the fail-closed gate shared with the
sibling P7 dataset — wired to ``FINANCEIRO_STOCK_INVENTORY_ENABLED``
(default off).
"""

from __future__ import annotations

from app.application.use_cases.financeiro_stock_movements.export_stock_movements_use_case import (
    ExportStockMovementsUseCase,
)
from app.application.use_cases.financeiro_stock_movements.get_stock_movements_use_case import (
    GetStockMovementsUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_stock_movements.stock_movements_repository import (
    StockMovementsRepository,
)


def build_stock_movements_use_case() -> GetStockMovementsUseCase:
    return GetStockMovementsUseCase(
        repository=StockMovementsRepository(),
        scope_resolver=get_stock_inventory_scope_resolver(),
    )


def build_export_stock_movements_use_case() -> ExportStockMovementsUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportStockMovementsUseCase(
        get_use_case=build_stock_movements_use_case()
    )
