"""Composer for the R08 work-in-process report (MATR989, doc 80 §41).

Same dataset-scope resolver and repository as the P7 engine — the
standalone report is a second surface over the identical rule.
"""

from __future__ import annotations

from app.application.use_cases.financeiro_work_in_process.export_work_in_process_use_case import (
    ExportWorkInProcessUseCase,
)
from app.application.use_cases.financeiro_work_in_process.get_work_in_process_use_case import (
    GetWorkInProcessUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_stock_inventory.stock_inventory_repository import (
    StockInventoryRepository,
)


def build_work_in_process_use_case() -> GetWorkInProcessUseCase:
    return GetWorkInProcessUseCase(
        repository=StockInventoryRepository(),
        scope_resolver=get_stock_inventory_scope_resolver(),
    )


def build_export_work_in_process_use_case() -> ExportWorkInProcessUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportWorkInProcessUseCase(
        get_use_case=build_work_in_process_use_case()
    )
