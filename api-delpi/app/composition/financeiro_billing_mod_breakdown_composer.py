"""Composer for the R09 billing × MOD breakdown (doc 141, DR-1/DR-2).

Same shared-dataset fail-closed gate the sibling financeiro family uses
(``FINANCEIRO_STOCK_INVENTORY_ENABLED``, doc 49 §8): dedicated S2S
client + delegated human principal are enforced at the route layer.
"""

from __future__ import annotations

from app.application.use_cases.financeiro_billing_mod_breakdown.get_billing_mod_breakdown_use_case import (
    GetBillingModBreakdownUseCase,
)
from app.composition.financeiro_stock_inventory_composer import (
    get_stock_inventory_scope_resolver,
)
from app.infrastructure.persistence.totvs.financeiro_billing_mod_breakdown.billing_mod_breakdown_repository import (
    BillingModBreakdownRepository,
)


def build_billing_mod_breakdown_use_case() -> GetBillingModBreakdownUseCase:
    return GetBillingModBreakdownUseCase(
        repository=BillingModBreakdownRepository(),
        scope_resolver=get_stock_inventory_scope_resolver(),
    )
