"""E-LMP-01 — listagem funcional de LMPs (regras na Engineering API).

Fluxo (paridade com `ListLMPDashboardUseCase` legado):
  facts F-LMP-01 (dataset staged oficial, todas as páginas)
  → reclassificação S05/S07 sobre flags declaradas (owner semântico)
  → enriquecimento R01–R05/R08 por item
  → filtro de status funcional
  → paginação + summary R09/R10 + charts R11

Fatos chegam já qualificados pela política de período/residência (push-down
documentado na spec S03/S06 — a execução física permanece na fonte); a
reclassificação efetiva é reaplicada aqui como autoridade semântica e é a
base dos testes de paridade contra o valor executado na fonte.
"""

from __future__ import annotations

from typing import Any

from engineering_app.application.models.lmp import (
    LmpDashboardItem,
    LmpFact,
    LmpQuery,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.lmp_facts import LmpFactsSource
from engineering_app.domain.lmp.business_rules import compute_dashboard_fields
from engineering_app.domain.lmp.dashboard_aggregates import (
    build_charts,
    compute_summary,
    filter_items_by_status,
    is_lmp,
    resolve_dashboard_status_filter,
)
from engineering_app.domain.lmp.listing_semantics import (
    effective_listing_kind,
    resolve_listing_type_filter,
)

DEFAULT_PAGE_SIZE = 50
FACTS_PAGE_SIZE = 500
MAX_FACTS_PAGES = 40  # teto de segurança: 20k linhas de fato por consulta


def enrich_fact(fact: LmpFact) -> LmpDashboardItem:
    """R08 — item funcional a partir do fato (R01–R05 + S05/S07)."""
    computed = compute_dashboard_fields(
        start_date_str=fact.start_date,
        end_date_str=fact.end_date,
        qtd_pi=fact.qtd_pi,
        engineering_status=fact.engineering_status,
        engineering_total_minutes=fact.residence_minutes,
    )
    listing_kind = effective_listing_kind(
        anchor_kind=fact.listing_kind_source,
        has_sample_anchor=fact.has_sample_anchor,
        sample_minutes=fact.sample_eng_minutes,
        total_minutes=int(fact.residence_minutes or 0),
        has_lmp_finalized=fact.has_lmp_finalized,
    )

    return LmpDashboardItem(
        branch=fact.branch,
        sale_number=fact.sale_number,
        sale_description=fact.sale_description,
        listing_kind=listing_kind,
        start_date=fact.start_date,
        end_date=fact.end_date,
        nivel=computed.level,
        dias_uteis_sla=computed.sla_days,
        sla_minutos=computed.sla_minutes,
        engineering_total_minutes=int(fact.residence_minutes or 0),
        data_limite=computed.data_limite,
        lead_time_util=computed.lead_time_util,
        status=computed.status,
        homolog_revision=fact.homolog_revision,
        measurement_revision=fact.measurement_revision,
        homolog_date=fact.homolog_date or fact.start_date,
        cycle_index=fact.cycle_index,
        engineering_status=fact.engineering_status,
        qtd_pi=fact.qtd_pi,
    )


class ListLmpsDashboardUseCase:
    """E-LMP-01 — composição funcional sobre o contrato facts."""

    def __init__(self, facts_source: LmpFactsSource):
        self._facts = facts_source

    async def _load_all_facts(
        self,
        ctx: HomeSourceContext,
        query: LmpQuery,
        *,
        include_qtd_pi: bool,
        listing_type: str | None,
    ):
        first = await self._facts.fetch_facts(
            ctx,
            start_date=query.start_date,
            end_date=query.end_date,
            branch=query.branch,
            listing_type=listing_type,
            page=1,
            page_size=FACTS_PAGE_SIZE,
            include_qtd_pi=include_qtd_pi,
        )
        if first.status != "available" or first.total is None:
            return first

        facts = list(first.facts)
        total = first.total
        page = 1
        while len(facts) < total and page < MAX_FACTS_PAGES:
            page += 1
            nxt = await self._facts.fetch_facts(
                ctx,
                start_date=query.start_date,
                end_date=query.end_date,
                branch=query.branch,
                listing_type=listing_type,
                page=page,
                page_size=FACTS_PAGE_SIZE,
                include_qtd_pi=include_qtd_pi,
            )
            if nxt.status != "available":
                return type(first)(
                    status="unavailable",
                    reason=nxt.reason or "pagination_error",
                    provenance=first.provenance,
                    policy=first.policy,
                )
            facts.extend(nxt.facts)

        return type(first)(
            status=first.status,
            facts=tuple(facts),
            total=total,
            provenance=first.provenance,
            policy=first.policy,
        )

    async def execute(
        self,
        ctx: HomeSourceContext,
        query: LmpQuery,
    ) -> dict[str, Any]:
        resolved_listing = resolve_listing_type_filter(query.listing_type)
        resolved_status = resolve_dashboard_status_filter(query.status_filter)

        result = await self._load_all_facts(
            ctx,
            query,
            include_qtd_pi=True,
            listing_type=query.listing_type or resolved_listing,
        )
        if result.status != "available":
            return {
                "status": result.status,
                "reason": result.reason,
                "message": result.message,
                "items": [],
                "total": 0,
            }

        enriched = [enrich_fact(fact) for fact in result.facts]
        if resolved_listing:
            enriched = [
                item for item in enriched if item.listing_kind == resolved_listing
            ]
        filtered = filter_items_by_status(enriched, resolved_status)
        lmp_only = [item for item in enriched if is_lmp(item)]

        total = len(filtered)
        page = max(int(query.page or 1), 1)
        page_size = int(query.page_size or DEFAULT_PAGE_SIZE)
        start = (page - 1) * page_size
        paginated = filtered[start : start + page_size]

        return {
            "status": "available",
            "items": [item.to_dict() for item in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": compute_summary(lmp_only, total),
            "charts": build_charts(filtered),
            "provenance": result.provenance,
            "policy": result.policy,
        }
