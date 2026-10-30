"""Composer for the R10 cost-center-expenses report (doc 126).

The dataset-scope resolver is the same fail-closed gate the sibling
stock-inventory family uses — wired to
``FINANCEIRO_STOCK_INVENTORY_ENABLED`` (default off): the reports share
one authorized Protheus dataset (doc 49 §8).
"""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_cost_center_expenses.export_cost_center_expenses_use_case import (
    ExportCostCenterExpensesUseCase,
)
from app.application.use_cases.financeiro_cost_center_expenses.list_cost_center_expenses_use_case import (
    ListCostCenterExpensesUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_cost_center_expenses.cost_center_expenses_repository import (
    CostCenterExpensesRepository,
)


def _scope_resolver() -> StockInventoryScopeResolver:
    return get_stock_inventory_scope_resolver()


def build_cost_center_expenses_use_case() -> ListCostCenterExpensesUseCase:
    return ListCostCenterExpensesUseCase(
        repository=CostCenterExpensesRepository(),
        scope_resolver=_scope_resolver(),
    )


def build_export_cost_center_expenses_use_case() -> ExportCostCenterExpensesUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportCostCenterExpensesUseCase(
        get_use_case=build_cost_center_expenses_use_case()
    )
