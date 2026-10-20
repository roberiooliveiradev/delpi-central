from app.application.security.settlement_scope import (
    UnresolvedSettlementScopeResolver,
)
from app.application.use_cases.financeiro_settlements.get_settlements_use_case import (
    GetSettlementsUseCase,
)
from app.application.use_cases.financeiro_settlements.get_summary_use_case import (
    GetSettlementsSummaryUseCase,
)
from app.infrastructure.persistence.totvs.financeiro_settlements.settlements_repository import (
    SettlementsRepository,
)


def _repository() -> SettlementsRepository:
    return SettlementsRepository()


def _scope_resolver() -> UnresolvedSettlementScopeResolver:
    # Fail-closed default (doc 48 D3.1): no proven dataset-scope mechanism
    # exists yet, so real settlement rows stay unavailable until an approved
    # resolver implementation is wired here.
    return UnresolvedSettlementScopeResolver()


def build_get_settlements_use_case() -> GetSettlementsUseCase:
    return GetSettlementsUseCase(
        repository=_repository(),
        scope_resolver=_scope_resolver(),
    )


def build_get_settlements_summary_use_case() -> GetSettlementsSummaryUseCase:
    return GetSettlementsSummaryUseCase(
        repository=_repository(),
        scope_resolver=_scope_resolver(),
    )
