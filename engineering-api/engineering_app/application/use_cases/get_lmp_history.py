"""E-LMP-04/05 — histórico funcional de uma OV (eventos e fluxo).

Fatos crus via F-LMP-03 (api-delpi) → enriquecimento do domínio migrado:
- `events`: `enrich_history_events` (labels processo/estágio/status,
  flags open/late, revisão de referência do painel).
- `flow`: `enrich_flow_transition_fields` + labels de processo/estágio.

Datas chegam em ISO na borda facts; o parser do domínio aceita ISO e
Protheus — a serialização permanece ISO, sem reformatar.

Estados honestos: empty (sem eventos), forbidden, unavailable.
"""

from __future__ import annotations

from typing import Any

from engineering_app.application.models.lmp import LmpQuery
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.lmp_facts import LmpFactsSource
from engineering_app.domain.lmp.flow_transition import (
    enrich_flow_transition_fields,
)
from engineering_app.domain.lmp.history_enrichment import (
    enrich_history_events,
    resolve_process_label,
    resolve_stage_label,
)

VALID_VIEWS = ("events", "flow")


class GetLmpHistoryUseCase:
    """Histórico da OV — regras Engineering API sobre fatos oficiais."""

    def __init__(self, facts_source: LmpFactsSource, *, view: str):
        if view not in VALID_VIEWS:
            raise ValueError(f"view inválida: {view}")
        self._facts = facts_source
        self._view = view

    async def execute(
        self,
        ctx: HomeSourceContext,
        query: LmpQuery,
    ) -> dict[str, Any]:
        result = await self._facts.fetch_history(
            ctx,
            sale_number=str(query.sale_number or ""),
            view=self._view,
            start_date=query.start_date,
            end_date=query.end_date,
            branch=query.branch,
            revision=query.revision,
        )
        if result.status not in ("available", "empty"):
            return {
                "status": result.status,
                "reason": result.reason,
                "message": result.message,
            }

        raw_items = [dict(item) for item in result.items]
        if self._view == "events":
            items = enrich_history_events(
                raw_items,
                reference_revision=result.reference_revision,
            )
        else:
            items = [
                {
                    **enrich_flow_transition_fields(event),
                    "process_label": resolve_process_label(event),
                    "stage_label": resolve_stage_label(event),
                }
                for event in raw_items
            ]

        return {
            "status": result.status,
            "sale_number": str(query.sale_number or ""),
            "branch": result.branch or query.branch,
            "reference_revision": result.reference_revision,
            "panel_start_date": result.panel_start_date,
            "view": self._view,
            "items": items,
            "total": len(items),
            "provenance": result.provenance,
        }
