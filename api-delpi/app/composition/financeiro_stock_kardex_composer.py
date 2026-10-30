"""Composer for the R06/R07 stock-kardex reports (doc 122).

The dataset-scope resolver is the same fail-closed gate the sibling
stock-inventory family uses — wired to
``FINANCEIRO_STOCK_INVENTORY_ENABLED`` (default off): the reports share
one authorized Protheus dataset (doc 49 §8).
"""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_stock_kardex.export_stock_kardex_use_case import (
    ExportStockKardexUseCase,
)
from app.application.use_cases.financeiro_stock_kardex.get_financeiro_cpv_use_case import (
    GetFinanceiroCpvUseCase,
)
from app.application.use_cases.financeiro_stock_kardex.get_stock_kardex_summary_use_case import (
    GetStockKardexSummaryUseCase,
)
from app.application.use_cases.financeiro_stock_kardex.get_stock_kardex_use_case import (
    GetStockKardexUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_stock_kardex.stock_kardex_repository import (
    StockKardexRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.cpv_query_repository import (
    CpvQueryRepository,
)


def _scope_resolver() -> StockInventoryScopeResolver:
    return get_stock_inventory_scope_resolver()


def build_stock_kardex_use_case() -> GetStockKardexUseCase:
    return GetStockKardexUseCase(
        repository=StockKardexRepository(),
        scope_resolver=_scope_resolver(),
    )


def build_stock_kardex_summary_use_case() -> GetStockKardexSummaryUseCase:
    return GetStockKardexSummaryUseCase(
        repository=StockKardexRepository(),
        scope_resolver=_scope_resolver(),
    )


def build_export_stock_kardex_use_case() -> ExportStockKardexUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportStockKardexUseCase(
        get_use_case=build_stock_kardex_use_case()
    )


def build_financeiro_cpv_use_case() -> GetFinanceiroCpvUseCase:
    """Dedicated CPV contract (D-O1) — canonical CPV semantics inside
    the governed financeiro envelope."""
    return GetFinanceiroCpvUseCase(
        cpv_repository=CpvQueryRepository(),
        scope_resolver=_scope_resolver(),
    )
