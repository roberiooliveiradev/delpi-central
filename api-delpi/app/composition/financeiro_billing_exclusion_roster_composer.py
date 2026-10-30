"""Composer for the R11 billing-exclusion roster (doc 126).

The dataset-scope resolver is the same fail-closed gate the sibling
stock-inventory family uses — wired to
``FINANCEIRO_STOCK_INVENTORY_ENABLED`` (default off): the reports share
one authorized Protheus dataset (doc 49 §8).
"""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    StockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_billing_exclusion_roster.export_billing_exclusion_roster_use_case import (
    ExportBillingExclusionRosterUseCase,
)
from app.application.use_cases.financeiro_billing_exclusion_roster.list_billing_exclusion_roster_use_case import (
    ListBillingExclusionRosterUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_billing_exclusion_roster.billing_exclusion_roster_repository import (
    BillingExclusionRosterRepository,
)


def _scope_resolver() -> StockInventoryScopeResolver:
    return get_stock_inventory_scope_resolver()


def build_billing_exclusion_roster_use_case() -> ListBillingExclusionRosterUseCase:
    return ListBillingExclusionRosterUseCase(
        repository=BillingExclusionRosterRepository(),
        scope_resolver=_scope_resolver(),
    )


def build_export_billing_exclusion_roster_use_case() -> ExportBillingExclusionRosterUseCase:
    """Export composes the SAME query use case — one engine, one rule."""
    return ExportBillingExclusionRosterUseCase(
        get_use_case=build_billing_exclusion_roster_use_case()
    )
