"""Composition root — wiring dos casos de uso LMP (G3/G4.A.R1).

Único ponto que conhece URLs concretas e constrói o adapter facts real —
ports e use cases permanecem livres de HTTP/infra.

S2S: o provider de token client-credentials é instanciado lazy na
primeira chamada — configuração ausente falha fechado no adapter
(`unavailable`), nunca impede o boot nem produz bypass.
"""

from __future__ import annotations


from engineering_app.application.use_cases.get_lmp_detail import (
    GetLmpDetailUseCase,
)
from engineering_app.application.use_cases.get_lmp_history import (
    GetLmpHistoryUseCase,
)
from engineering_app.application.use_cases.get_lmp_summary import (
    GetLmpSummaryUseCase,
)
from engineering_app.application.use_cases.list_lmps_dashboard import (
    ListLmpsDashboardUseCase,
)
from engineering_app.config import settings
from engineering_app.infrastructure.gateways.api_delpi_facts import (
    ApiDelpiFactsSource,
)
from engineering_app.infrastructure.gateways.delegated_auxiliary import (
    ApiDelpiDelegatedAuxiliary,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)

from engineering_app.infrastructure.gateways.s2s_token import (
    get_s2s_service_token as _s2s_service_token,
    reset_s2s_provider as _reset_s2s_provider,
)


def _build_facts_source() -> ApiDelpiFactsSource:
    client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=settings.LMP_FACTS_TIMEOUT_SECONDS,
    )
    return ApiDelpiFactsSource(client, _s2s_service_token)


def build_list_lmps_dashboard_use_case() -> ListLmpsDashboardUseCase:
    return ListLmpsDashboardUseCase(_build_facts_source())


def build_get_lmp_summary_use_case() -> GetLmpSummaryUseCase:
    return GetLmpSummaryUseCase(_build_facts_source())


def build_get_lmp_detail_use_case() -> GetLmpDetailUseCase:
    return GetLmpDetailUseCase(_build_facts_source())


def build_get_lmp_history_use_case(*, view: str) -> GetLmpHistoryUseCase:
    return GetLmpHistoryUseCase(_build_facts_source(), view=view)


def build_delegated_auxiliary_source() -> ApiDelpiDelegatedAuxiliary:
    return ApiDelpiDelegatedAuxiliary(
        DownstreamClient(
            settings.DELPI_API_URL,
            timeout_seconds=settings.LMP_FACTS_TIMEOUT_SECONDS,
        )
    )
