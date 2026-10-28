"""Use case — Visão geral do Portal Engenharia (F3.OVERVIEW).

Composição paralela das famílias oficiais (LMP, TRANSFORMA+) + scores
do Strategic Indicators. Falha de uma família preserva os indicadores
da outra (`partial`); falha do SI deixa `idd=None` sem apagar dados —
o owner das metas enriquece o payload dos próprios resumos. Nenhum
valor é inventado, recalculado ou substituído por zero.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from engineering_app.application.models.overview import (
    OverviewFilters,
    OverviewIndicator,
    OverviewResponse,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.overview_sources import (
    IndicatorFetch,
    OverviewFamilySource,
    OverviewQuery,
    OverviewSiSource,
)
from engineering_app.infrastructure.gateways.overview_api_delpi import (
    SI_IDD_BY_INDICATOR,
)

logger = logging.getLogger(__name__)

# IDs/labels estáveis do contrato — família falha/empty também emite
# os indicadores com `availability` real, sem inventar valores.
_FAMILY_INDICATORS = {
    "lmp": {
        "lmp_on_time": "% LMP dentro do prazo",
        "lmp_lead_time": "Lead time médio",
        "lmp_total_proposals": "Total de propostas",
    },
    "transforma": {
        "transforma_gross_savings": "Ganhos brutos TRANSFORMA+",
        "transforma_solutions": "Soluções implementadas",
        "transforma_roi": "ROI médio TRANSFORMA+",
    },
}

_AVAILABILITY_BY_STATUS = {
    "available": "available",
    "empty": "empty",
    "unavailable": "unavailable",
    "forbidden": "forbidden",
}


class GetEngineeringOverviewUseCase:
    def __init__(
        self,
        lmp_source: OverviewFamilySource,
        transforma_source: OverviewFamilySource,
        si_source: OverviewSiSource | None = None,
        source_timeout_seconds: float = 8.0,
        max_concurrent_sources: int = 3,
    ) -> None:
        self._sources = {"lmp": lmp_source, "transforma": transforma_source}
        self._si_source = si_source
        self._timeout = source_timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent_sources)

    async def _fetch_family(
        self, name: str, ctx: HomeSourceContext, query: OverviewQuery
    ) -> IndicatorFetch:
        source = self._sources[name]
        try:
            async with self._semaphore:
                return await asyncio.wait_for(
                    source.fetch(ctx, query=query), timeout=self._timeout
                )
        except TimeoutError:
            return IndicatorFetch(
                status="unavailable",
                reason="timeout",
                message="Fonte oficial excedeu o tempo limite.",
            )
        except Exception:
            logger.warning(
                "overview_family_fetch_failed family=%s system=%s",
                name,
                source.system,
                exc_info=True,
            )
            return IndicatorFetch(status="unavailable", reason="upstream_error")

    async def _fetch_si_scores(
        self, ctx: HomeSourceContext, query: OverviewQuery
    ) -> dict[str, float] | None:
        if self._si_source is None:
            return None
        try:
            return await asyncio.wait_for(
                self._si_source.fetch_scores(ctx, query=query),
                timeout=self._timeout,
            )
        except Exception:
            logger.warning("overview_si_scores_fetch_failed", exc_info=True)
            return None

    @staticmethod
    def _attach_idd(
        indicators: tuple[OverviewIndicator, ...],
        scores: dict[str, float] | None,
    ) -> list[OverviewIndicator]:
        if not scores:
            return list(indicators)
        merged: list[OverviewIndicator] = []
        for ind in indicators:
            si_id = SI_IDD_BY_INDICATOR.get(ind.id)
            if si_id and si_id in scores:
                merged.append(
                    ind.model_copy(
                        update={"idd": scores[si_id], "idd_label": si_id}
                    )
                )
            else:
                merged.append(ind)
        return merged

    async def execute(
        self, ctx: HomeSourceContext, *, query: OverviewQuery
    ) -> OverviewResponse:
        lmp, transforma, scores = await asyncio.gather(
            self._fetch_family("lmp", ctx, query),
            self._fetch_family("transforma", ctx, query),
            self._fetch_si_scores(ctx, query),
        )

        families = {"lmp": lmp, "transforma": transforma}
        usable = sum(
            1 for f in families.values() if f.status in ("available", "empty")
        )
        if usable == len(families):
            status = "available"
        elif usable:
            status = "partial"
        else:
            status = "unavailable"

        indicators: list[OverviewIndicator] = []
        for family_id, fetch in families.items():
            if fetch.indicators:
                indicators.extend(fetch.indicators)
                continue
            # Família sem payload (empty/unavailable/forbidden/timeout):
            # emite os indicadores com availability real, sem valor.
            source = self._sources[family_id]
            for indicator_id, label in _FAMILY_INDICATORS[family_id].items():
                indicators.append(
                    OverviewIndicator(
                        id=indicator_id,
                        label=label,
                        family=family_id,
                        availability=_AVAILABILITY_BY_STATUS[fetch.status],
                        scope="consolidado",
                        start_date=query.start_date,
                        end_date=query.end_date,
                        source=source.system,
                        source_endpoint=source.endpoint,
                        reason=fetch.reason,
                        message=fetch.message,
                    )
                )

        indicators = self._attach_idd(tuple(indicators), scores)

        return OverviewResponse(
            generated_at=datetime.now(timezone.utc).isoformat(),
            filters=OverviewFilters(
                start_date=query.start_date,
                end_date=query.end_date,
                competence=query.competence,
                branch=query.branch,
            ),
            status=status,
            indicators=indicators,
        )
