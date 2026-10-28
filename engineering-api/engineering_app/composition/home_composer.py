"""Composition root — wiring do caso de uso da Home (F2a.S3/S4).

Único ponto que conhece URLs concretas e constrói os gateways reais —
ports e use case permanecem livres de HTTP/infra.
"""

from __future__ import annotations

from engineering_app.application.use_cases.get_engineering_home import (
    GetEngineeringHome,
)
from engineering_app.config import settings
from engineering_app.infrastructure.gateways.api_delpi_gateway import (
    ApiDelpiLmpSource,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)
from engineering_app.infrastructure.gateways.requests_api_gateway import (
    RequestsApiMineSource,
    RequestsApiWorkQueueSource,
)


def build_get_engineering_home_use_case() -> GetEngineeringHome:
    timeout = settings.HOME_SOURCE_TIMEOUT_SECONDS

    requests_client = DownstreamClient(
        settings.REQUESTS_API_URL,
        timeout_seconds=timeout,
    )
    delpi_client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=timeout,
    )

    return GetEngineeringHome(
        tasks_source=RequestsApiWorkQueueSource(requests_client),
        requests_source=RequestsApiMineSource(requests_client),
        lmps_source=ApiDelpiLmpSource(delpi_client),
        section_limit=settings.HOME_MAX_SECTION_ITEMS,
        source_timeout_seconds=timeout,
        max_concurrent_sources=settings.HOME_MAX_CONCURRENT_SOURCES,
    )
