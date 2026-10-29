"""E-LMP-02 — detalhe funcional de uma OV/LMP (paridade `/lmps/{sale}`).

Fato oficial via F-LMP-02 (api-delpi, header + produtos + cliente/vendedor)
→ enriquecimento do domínio migrado (nivel/SLA/data_limite/lead/status —
R01–R05). `list_history` segue o contrato legado: sempre vazio aqui — o
histórico é servido pelas rotas dedicadas E-LMP-04/05.

Estados honestos: not_found (OV ausente na listagem de engenharia),
forbidden, unavailable — nunca payload inventado.
"""

from __future__ import annotations

from typing import Any

from engineering_app.application.models.lmp import LmpQuery
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.lmp_facts import LmpFactsSource
from engineering_app.domain.lmp.business_rules import compute_dashboard_fields
from engineering_app.domain.lmp.dates import format_date_iso


class GetLmpDetailUseCase:
    """Detalhe da OV — regras Engineering API sobre fato oficial."""

    def __init__(self, facts_source: LmpFactsSource):
        self._facts = facts_source

    async def execute(
        self,
        ctx: HomeSourceContext,
        query: LmpQuery,
    ) -> dict[str, Any]:
        result = await self._facts.fetch_fact(
            ctx,
            sale_number=str(query.sale_number or ""),
            start_date=query.start_date,
            end_date=query.end_date,
            branch=query.branch,
            include=None,
        )
        if result.status != "available" or not isinstance(result.fact, dict):
            return {
                "status": result.status,
                "reason": result.reason,
                "message": result.message,
            }

        item = dict(result.fact)
        fields = compute_dashboard_fields(
            start_date_str=item.get("start_date"),
            end_date_str=item.get("end_date"),
            qtd_pi=item.get("qtd_pi"),
            engineering_status=item.get("engineering_status"),
            engineering_total_minutes=item.get("engineering_total_minutes"),
        )
        item["nivel"] = fields.level
        item["dias_uteis_sla"] = fields.sla_days
        item["sla_minutos"] = fields.sla_minutes
        item["data_limite"] = format_date_iso(fields.data_limite)
        item["lead_time_util"] = fields.lead_time_util
        item["status"] = fields.status
        # Contrato legado: histórico embutido sempre vazio no detalhe —
        # as rotas dedicadas de histórico atendem o painel completo.
        item["list_history"] = []

        return {
            "status": "available",
            "item": item,
            "provenance": result.provenance,
        }
