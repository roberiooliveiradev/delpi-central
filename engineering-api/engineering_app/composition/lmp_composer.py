"""Composition root — wiring dos casos de uso LMP (G3/G4.A.R1).

Único ponto que conhece URLs concretas e constrói o adapter facts real —
ports e use cases permanecem livres de HTTP/infra.

S2S: o provider de token client-credentials é instanciado lazy na
primeira chamada — configuração ausente falha fechado no adapter
(`unavailable`), nunca impede o boot nem produz bypass.
"""

from __future__ import annotations

import threading

from delpi_auth.service_token_provider import ClientCredentialsTokenProvider

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
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)

_provider_lock = threading.Lock()
_shared_provider: ClientCredentialsTokenProvider | None = None


def _s2s_service_token() -> str:
    """Token client-credentials desta API — cache process-wide (mesmo
    padrão controllership-finance-api/supplies-api)."""
    global _shared_provider
    if _shared_provider is None:
        with _provider_lock:
            if _shared_provider is None:
                _shared_provider = ClientCredentialsTokenProvider.from_env()
    return _shared_provider.get_token()


def _reset_s2s_provider() -> None:
    """Test hook — descarta o provider cacheado para recarregar env."""
    global _shared_provider
    with _provider_lock:
        _shared_provider = None


def _build_facts_source() -> ApiDelpiFactsSource:
    client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=settings.HOME_SOURCE_TIMEOUT_SECONDS,
    )
    return ApiDelpiFactsSource(client, _s2s_service_token)


def build_list_lmps_dashboard_use_case() -> ListLmpsDashboardUseCase:
    return ListLmpsDashboardUseCase(_build_facts_source())


def build_get_lmp_summary_use_case() -> GetLmpSummaryUseCase:
    return GetLmpSummaryUseCase(_build_facts_source())
