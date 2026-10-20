from app.application.security.settlement_scope import (
    SettlementScopeResolver,
    SharedDatasetSettlementScopeResolver,
)
from app.application.use_cases.financeiro_settlements.get_settlements_use_case import (
    GetSettlementsUseCase,
)
from app.application.use_cases.financeiro_settlements.get_summary_use_case import (
    GetSettlementsSummaryUseCase,
)
from app.config import settings
from app.infrastructure.persistence.totvs.financeiro_settlements.settlements_repository import (
    SettlementsRepository,
)


def _repository() -> SettlementsRepository:
    return SettlementsRepository()


def _scope_resolver() -> SettlementScopeResolver:
    # D3 shared dataset (doc 48): resolves only when the separate enablement
    # gate is on AND a delegated human principal is present; fail-closed
    # otherwise.
    return SharedDatasetSettlementScopeResolver(
        shared_dataset_enabled=settings.FINANCEIRO_SETTLEMENTS_SHARED_DATASET_ENABLED,
    )


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
