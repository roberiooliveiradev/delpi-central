"""Composition root — wiring dos casos de uso LMP (G3).

Único ponto que conhece URLs concretas e constrói o adapter facts real —
ports e use cases permanecem livres de HTTP/infra.
"""

from __future__ import annotations

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


def _build_facts_source() -> ApiDelpiFactsSource:
    client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=settings.HOME_SOURCE_TIMEOUT_SECONDS,
    )
    return ApiDelpiFactsSource(client)


def build_list_lmps_dashboard_use_case() -> ListLmpsDashboardUseCase:
    return ListLmpsDashboardUseCase(_build_facts_source())


def build_get_lmp_summary_use_case() -> GetLmpSummaryUseCase:
    return GetLmpSummaryUseCase(_build_facts_source())
