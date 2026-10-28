"""Composition root — wiring do caso de uso da Visão geral (F3.OVERVIEW).

Único ponto que conhece URLs concretas e constrói os gateways reais —
ports e use case permanecem livres de HTTP/infra.
"""

from __future__ import annotations

from engineering_app.application.use_cases.get_engineering_overview import (
    GetEngineeringOverviewUseCase,
)
from engineering_app.config import settings
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)
from engineering_app.infrastructure.gateways.overview_api_delpi import (
    ApiDelpiEngineeringSiSource,
    ApiDelpiLmpOverviewSource,
    ApiDelpiTransformaOverviewSource,
)


def build_get_engineering_overview_use_case() -> GetEngineeringOverviewUseCase:
    timeout = settings.HOME_SOURCE_TIMEOUT_SECONDS

    delpi_client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=timeout,
    )

    return GetEngineeringOverviewUseCase(
        lmp_source=ApiDelpiLmpOverviewSource(delpi_client),
        transforma_source=ApiDelpiTransformaOverviewSource(delpi_client),
        si_source=ApiDelpiEngineeringSiSource(delpi_client),
        source_timeout_seconds=timeout,
        max_concurrent_sources=settings.HOME_MAX_CONCURRENT_SOURCES,
    )
