"""E-LMP-03 — summary realizado de LMPs (sem metas/IDD — owner: SI).

Equivalente ao modo `kpi` do dashboard legado: facts sem PI (F-LMP-01) +
contagem PI em lote apenas para OVs FINALIZADA (F-LMP-04) → R09/R10.
Nunca enriquece `goal_*` nem chama Strategic Indicators — o realizado é
entregue puro para o consumer de metas compor (transição C→A, doc 33 §10).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from engineering_app.application.models.lmp import LmpFact, LmpQuery
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.lmp_facts import LmpFactsSource
from engineering_app.application.use_cases.list_lmps_dashboard import (
    FACTS_PAGE_SIZE,
    MAX_FACTS_PAGES,
    enrich_fact,
)
from engineering_app.domain.lmp.business_rules import is_engineering_finished
from engineering_app.domain.lmp.dashboard_aggregates import compute_summary, is_lmp
from engineering_app.domain.lmp.listing_semantics import (
    facts_listing_type_param,
    resolve_listing_type_filter,
)


def _ov_key(fact: LmpFact) -> dict[str, str] | None:
    """Chave F-LMP-04 — mesma resolução do legado (homolog→measurement)."""
    branch = str(fact.branch or "").strip()
    sale_number = str(fact.sale_number or "").strip()
    revision = str(
        fact.homolog_revision or fact.measurement_revision or ""
    ).strip()
    if not branch or not sale_number or not revision:
        return None
    return {"branch": branch, "sale_number": sale_number, "revision": revision}


class GetLmpSummaryUseCase:
    """E-LMP-03 — KPIs realizados de LMP (owner das regras: eng-api)."""

    def __init__(self, facts_source: LmpFactsSource):
        self._facts = facts_source

    async def _load_facts(self, ctx: HomeSourceContext, query: LmpQuery):
        facts: list[LmpFact] = []
        page = 1
        total = None
        provenance: dict[str, Any] = {}
        policy: dict[str, Any] = {}
        while page <= MAX_FACTS_PAGES:
            result = await self._facts.fetch_facts(
                ctx,
                start_date=query.start_date,
                end_date=query.end_date,
                branch=query.branch,
                listing_type=facts_listing_type_param(
                    resolve_listing_type_filter(
                        query.listing_type, lmp_only=True
                    )
                ),
                page=page,
                page_size=FACTS_PAGE_SIZE,
                include_qtd_pi=False,
            )
            if result.status != "available":
                return result
            facts.extend(result.facts)
            total = result.total
            provenance = result.provenance
            policy = result.policy
            if total is None or len(facts) >= total:
                break
            page += 1
        return type(result)(
            status="available",
            facts=tuple(facts),
            total=total,
            provenance=provenance,
            policy=policy,
        )

    async def execute(
        self,
        ctx: HomeSourceContext,
        query: LmpQuery,
    ) -> dict[str, Any]:
        result = await self._load_facts(ctx, query)
        if result.status != "available":
            return {
                "status": result.status,
                "reason": result.reason,
                "message": result.message,
            }

        # R12 — política: PI só é necessária para OVs FINALIZADA.
        finished_keys: list[dict[str, str]] = []
        key_by_tuple: dict[tuple[str, str, str], dict[str, str]] = {}
        for fact in result.facts:
            if not is_engineering_finished(fact.engineering_status):
                continue
            key = _ov_key(fact)
            if key is not None:
                finished_keys.append(key)
                key_by_tuple[(key["branch"], key["sale_number"], key["revision"])] = key

        pi_status = "not_requested"
        pi_counts = {}
        if finished_keys:
            pi_result = await self._facts.fetch_pi_counts(
                ctx,
                ov_keys=finished_keys,
                branch=query.branch,
            )
            if pi_result.status == "available":
                pi_status = "available"
                pi_counts = dict(pi_result.counts)
            else:
                pi_status = f"unavailable:{pi_result.reason or 'unknown'}"

        enriched = []
        for fact in result.facts:
            key = _ov_key(fact)
            qtd_pi = 0
            if key is not None and is_engineering_finished(fact.engineering_status):
                qtd_pi = int(
                    pi_counts.get(
                        (key["branch"], key["sale_number"], key["revision"]), 0
                    )
                )
            enriched.append(enrich_fact(replace(fact, qtd_pi=qtd_pi)))

        lmp_only = [item for item in enriched if is_lmp(item)]
        summary = compute_summary(lmp_only, len(enriched))

        return {
            "status": "available",
            "total_lmps": summary["total_lmps"],
            "total_items": summary["total_items"],
            "percent_dentro_prazo": summary["percent_dentro_prazo"],
            "avg_lead_time": summary["avg_lead_time"],
            "pi_counts_status": pi_status,
            "provenance": result.provenance,
            "policy": result.policy,
        }
