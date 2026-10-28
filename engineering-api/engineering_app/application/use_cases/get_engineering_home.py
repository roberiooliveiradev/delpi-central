"""GetEngineeringHome — agregação das seções elegíveis da Home (F2a.S3).

Composição, não domínio: o use case chama os ports das fontes oficiais
com fan-out limitado, timeout por fonte e estados honestos — nenhuma
fonte indisponível apaga dados válidos de outra, e nenhuma ausência de
backend vira coleção vazia silenciosa.

Seções sem backend oficial comprovado no G0 recebem estado explícito:
- attention → unavailable (sem fonte dedicada hoje)
- activity → unavailable (sem fonte dedicada hoje)
- collaboration → not_implemented (ADR-004 pendente de decisão)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from engineering_app.application.models.home import (
    HomeResponse,
    HomeSection,
    HomeSections,
    SourceRef,
)
from engineering_app.application.ports.home_sources import (
    HomeSectionSource,
    HomeSourceContext,
    SectionFetch,
)

logger = logging.getLogger(__name__)

_NO_OFFICIAL_SOURCE = "no_official_source"


class GetEngineeringHome:
    def __init__(
        self,
        *,
        tasks_source: HomeSectionSource,
        requests_source: HomeSectionSource,
        lmps_source: HomeSectionSource,
        section_limit: int,
        source_timeout_seconds: float,
        max_concurrent_sources: int,
    ) -> None:
        self._sections: dict[str, HomeSectionSource] = {
            "tasks": tasks_source,
            "requests": requests_source,
            "lmps": lmps_source,
        }
        self._section_limit = section_limit
        self._timeout = source_timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent_sources)

    async def _fetch_section(
        self, name: str, source: HomeSectionSource, ctx: HomeSourceContext
    ) -> HomeSection:
        ref = SourceRef(system=source.system, endpoint=source.endpoint)
        try:
            async with self._semaphore:
                result = await asyncio.wait_for(
                    source.fetch(ctx, limit=self._section_limit),
                    timeout=self._timeout,
                )
        except TimeoutError:
            return HomeSection(
                status="unavailable",
                source=ref,
                reason="timeout",
                message="Fonte oficial excedeu o tempo limite.",
            )
        except Exception:
            logger.warning(
                "home_section_fetch_failed section=%s system=%s",
                name,
                source.system,
                exc_info=True,
            )
            return HomeSection(
                status="unavailable",
                source=ref,
                reason="upstream_error",
            )

        return HomeSection(
            status=result.status,
            source=ref,
            items=list(result.items),
            total=result.total,
            reason=result.reason,
            message=result.message,
        )

    async def execute(self, ctx: HomeSourceContext) -> HomeResponse:
        tasks, requests, lmps = await asyncio.gather(
            self._fetch_section("tasks", self._sections["tasks"], ctx),
            self._fetch_section("requests", self._sections["requests"], ctx),
            self._fetch_section("lmps", self._sections["lmps"], ctx),
        )

        fetched = (tasks, requests, lmps)
        usable = sum(1 for s in fetched if s.status in ("available", "empty"))
        if usable == len(fetched):
            home_status = "available"
        elif usable:
            home_status = "partial"
        else:
            home_status = "unavailable"

        return HomeResponse(
            generated_at=datetime.now(timezone.utc).isoformat(),
            status=home_status,
            sections=HomeSections(
                attention=HomeSection(
                    status="unavailable",
                    reason=_NO_OFFICIAL_SOURCE,
                    message="Fonte oficial ainda não disponível.",
                ),
                tasks=tasks,
                lmps=lmps,
                requests=requests,
                activity=HomeSection(
                    status="unavailable",
                    reason=_NO_OFFICIAL_SOURCE,
                    message="Fonte oficial ainda não disponível.",
                ),
                collaboration=HomeSection(
                    status="not_implemented",
                    message="Colaboração/Salas aguarda backend oficial (ADR-004).",
                ),
            ),
        )
