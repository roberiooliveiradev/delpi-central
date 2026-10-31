"""Composer for the R12/R15 closing-state marker read (doc 129).

Same shared-dataset scope resolver family as the financeiro stock reads —
gated by ``FINANCEIRO_CLOSING_STATE_ENABLED`` (default off), plus the
dedicated S2S client + delegated human principal at the route layer.
"""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    SharedDatasetStockInventoryScopeResolver,
    StockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_closing_state.get_closing_state_use_case import (
    GetClosingStateUseCase,
)
from app.config import settings
from app.infrastructure.persistence.totvs.financeiro_closing_state.closing_state_repository import (
    ClosingStateRepository,
)


def get_closing_state_scope_resolver() -> StockInventoryScopeResolver:
    return SharedDatasetStockInventoryScopeResolver(
        enabled=getattr(settings, "FINANCEIRO_CLOSING_STATE_ENABLED", False)
    )


def build_closing_state_use_case() -> GetClosingStateUseCase:
    return GetClosingStateUseCase(
        repository=ClosingStateRepository(),
        scope_resolver=get_closing_state_scope_resolver(),
    )
