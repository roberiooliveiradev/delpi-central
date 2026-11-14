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
from engineering_app.infrastructure.gateways.prc_home_sources import (
    PrcMineHomeSource,
    PrcQueueHomeSource,
)
from engineering_app.composition.prc_composer import build_prc_service


def build_get_engineering_home_use_case() -> GetEngineeringHome:
    timeout = settings.HOME_SOURCE_TIMEOUT_SECONDS

    delpi_client = DownstreamClient(
        settings.DELPI_API_URL,
        timeout_seconds=timeout,
    )

    # Opção A (ledger §31): tasks/requests passam a ser alimentadas pelos
    # casos PRC nativos in-process. Os registros corporativos da
    # requests-api deixam a Home, mas permanecem intactos no My Requests.
    return GetEngineeringHome(
        tasks_source=PrcQueueHomeSource(build_prc_service),
        requests_source=PrcMineHomeSource(build_prc_service),
        lmps_source=ApiDelpiLmpSource(delpi_client),
        section_limit=settings.HOME_MAX_SECTION_ITEMS,
        source_timeout_seconds=timeout,
        max_concurrent_sources=settings.HOME_MAX_CONCURRENT_SOURCES,
    )
