from __future__ import annotations

from typing import Any

from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_repository import (
    ProcessoRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import (
    RevisaoRepository,
)


class ProcessRevisionCompareService:
    """Comparativo de revisões de um processo (última competência com dados)."""

    def compare(self, processo_id: str) -> dict[str, Any] | None:
        processo = ProcessoRepository().get(processo_id)
        if not processo:
            return None

        revisoes = RevisaoRepository().list_by_processo(processo_id)
        raw = DashboardDataRepository().load_raw()
        raw_filtered = self._filter_raw_for_process(raw, processo_id)
        calc = DashboardCalculatorService()
        rows = calc.build_dashboard_rows(raw_filtered)

        by_revisao: dict[str, list[dict]] = {}
        for row in rows:
            rid = str(row.get("revisao_id") or "")
            if rid:
                by_revisao.setdefault(rid, []).append(row)

        items: list[dict[str, Any]] = []
        for revisao in revisoes:
            rid = str(revisao.get("revisao_id") or "")
            rev_rows = sorted(by_revisao.get(rid, []), key=lambda r: r.get("competencia") or "")
            latest = rev_rows[-1] if rev_rows else None
            totals = self._sum_revision_rows(rev_rows)
            items.append(
                {
                    "revisao_id": rid,
                    "versao_revisao": revisao.get("versao_revisao"),
                    "cenario_tipo": revisao.get("cenario_tipo"),
                    "revisao_ativa": bool(revisao.get("revisao_ativa")),
                    "data_inicio_vigencia": revisao.get("data_inicio_vigencia"),
                    "data_fim_vigencia": revisao.get("data_fim_vigencia"),
                    "ultima_competencia": latest.get("competencia") if latest else None,
                    "totais": totals,
                    "meses_com_dados": len(rev_rows),
                }
            )

        return {
            "processo": {
                "processo_id": processo_id,
                "codigo_processo": processo.get("codigo_processo"),
                "nome_processo": processo.get("nome_processo"),
                "familia_processo": processo.get("familia_processo"),
                "agrupador_ferramenta": processo.get("agrupador_ferramenta"),
            },
            "total_revisoes": len(items),
            "items": items,
        }

    def _filter_raw_for_process(self, raw, processo_id: str):
        from tm_app.domain.raw_data import TransformometroRawData

        processos = [p for p in raw.processos if str(p.get("processo_id")) == processo_id]
        revisao_ids = {
            str(r.get("revisao_id"))
            for r in raw.revisoes
            if str(r.get("processo_id")) == processo_id
        }
        return TransformometroRawData(
            processos=processos,
            revisoes=[r for r in raw.revisoes if str(r.get("revisao_id")) in revisao_ids],
            medicoes=[m for m in raw.medicoes if str(m.get("revisao_id")) in revisao_ids],
            investimentos=[
                i for i in raw.investimentos if str(i.get("revisao_id")) in revisao_ids
            ],
            recursos_compartilhados=raw.recursos_compartilhados,
            revisao_recursos_compartilhados=[
                v
                for v in raw.revisao_recursos_compartilhados
                if str(v.get("revisao_id")) in revisao_ids
            ],
        )

    def _sum_revision_rows(self, rows: list[dict]) -> dict[str, float]:
        if not rows:
            return {
                "economia_bruta": 0.0,
                "economia_liquida_mes": 0.0,
                "investimento_unico_mes": 0.0,
                "custo_recorrente_mes": 0.0,
                "horas_economizadas_mes": 0.0,
            }
        return {
            "economia_bruta": round(sum(float(r.get("economia_bruta") or 0) for r in rows), 2),
            "economia_liquida_mes": round(
                sum(float(r.get("economia_liquida_mes") or 0) for r in rows), 2
            ),
            "investimento_unico_mes": round(
                sum(float(r.get("investimento_unico_mes") or 0) for r in rows), 2
            ),
            "custo_recorrente_mes": round(
                sum(float(r.get("custo_recorrente_mes") or 0) for r in rows), 2
            ),
            "horas_economizadas_mes": round(
                sum(float(r.get("horas_economizadas_mes") or 0) for r in rows), 2
            ),
        }
