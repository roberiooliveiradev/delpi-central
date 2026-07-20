from __future__ import annotations

from typing import Any

from tm_app.application.services.dashboard_view_scope_service import count_active_filiais
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
        rows = calc.build_dashboard_rows(
            raw_filtered,
            escopo_unidades=count_active_filiais(),
        )

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
            volume_acima = bool(latest and latest.get("volume_acima_referencia"))
            volume_abaixo = bool(latest and latest.get("volume_abaixo_referencia"))
            categoria = (
                revisao.get("beneficio_calculo_categoria") or "economia_tempo"
            )
            items.append(
                {
                    "revisao_id": rid,
                    "versao_revisao": revisao.get("versao_revisao"),
                    "cenario_tipo": revisao.get("cenario_tipo"),
                    "beneficio_calculo_categoria": categoria,
                    "revisao_ativa": bool(revisao.get("revisao_ativa")),
                    "data_inicio_vigencia": revisao.get("data_inicio_vigencia"),
                    "data_fim_vigencia": revisao.get("data_fim_vigencia"),
                    "ultima_competencia": latest.get("competencia") if latest else None,
                    "totais": totals,
                    "breakdown": self._breakdown_from_rows(rev_rows),
                    "volume_acima_referencia": volume_acima,
                    "volume_abaixo_referencia": volume_abaixo,
                    "avisos": self._volume_avisos(
                        categoria=str(categoria),
                        volume_acima=volume_acima,
                        volume_abaixo=volume_abaixo,
                        delta_volume=float(totals.get("delta_volume") or 0),
                    ),
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
        target_resource_ids = {
            str(v.get("recurso_compartilhado_id"))
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("revisao_id")) in revisao_ids
            and v.get("recurso_compartilhado_id") is not None
        }

        # O comparativo calcula somente as revisoes do processo selecionado, mas
        # precisa enxergar todos os vinculos dos recursos usados por ele. Caso
        # contrario, o rateio igualitario considera apenas 1 vinculo e cobra o
        # custo integral do recurso no processo em vez de dividir entre todos os
        # vinculos ativos da competencia.
        related_resource_links = [
            v
            for v in raw.revisao_recursos_compartilhados
            if str(v.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resources = [
            r
            for r in raw.recursos_compartilhados
            if str(r.get("recurso_compartilhado_id")) in target_resource_ids
        ]
        related_resource_costs = [
            c
            for c in raw.recurso_custos
            if str(c.get("recurso_compartilhado_id")) in target_resource_ids
        ]

        instancia_ids = {
            str(r.get("instancia_id"))
            for r in raw.revisoes
            if str(r.get("revisao_id")) in revisao_ids and r.get("instancia_id")
        }

        return TransformometroRawData(
            processos=processos,
            processo_instancias=[
                i
                for i in raw.processo_instancias
                if str(i.get("processo_id")) == processo_id
                or str(i.get("instancia_id")) in instancia_ids
            ],
            revisoes=[r for r in raw.revisoes if str(r.get("revisao_id")) in revisao_ids],
            medicoes=[m for m in raw.medicoes if str(m.get("revisao_id")) in revisao_ids],
            investimentos=[
                i for i in raw.investimentos if str(i.get("revisao_id")) in revisao_ids
            ],
            recursos_compartilhados=related_resources,
            revisao_recursos_compartilhados=related_resource_links,
            recurso_custos=related_resource_costs,
        )

    def _sum_revision_rows(self, rows: list[dict]) -> dict[str, float]:
        if not rows:
            return {
                "economia_bruta": 0.0,
                "economia_liquida_mes": 0.0,
                "investimento_unico_mes": 0.0,
                "custo_recorrente_mes": 0.0,
                "custo_recursos_compartilhados_mes": 0.0,
                "investimento_total_mes": 0.0,
                "horas_economizadas_mes": 0.0,
                "ganho_capacidade": 0.0,
                "economia_reducao_volume": 0.0,
                "delta_volume": 0.0,
            }

        investimento_unico = sum(float(r.get("investimento_unico_mes") or 0) for r in rows)
        custo_recorrente = sum(float(r.get("custo_recorrente_mes") or 0) for r in rows)
        custo_recursos = sum(float(r.get("custo_recursos_compartilhados_mes") or 0) for r in rows)
        latest = rows[-1] if rows else {}

        return {
            "economia_bruta": round(sum(float(r.get("economia_bruta") or 0) for r in rows), 2),
            "economia_liquida_mes": round(
                sum(float(r.get("economia_liquida_mes") or 0) for r in rows), 2
            ),
            "investimento_unico_mes": round(investimento_unico, 2),
            "custo_recorrente_mes": round(custo_recorrente, 2),
            "custo_recursos_compartilhados_mes": round(custo_recursos, 2),
            "investimento_total_mes": round(
                investimento_unico + custo_recorrente + custo_recursos, 2
            ),
            "horas_economizadas_mes": round(
                sum(float(r.get("horas_economizadas_mes") or 0) for r in rows), 2
            ),
            "ganho_capacidade": round(
                sum(float(r.get("ganho_capacidade") or 0) for r in rows), 2
            ),
            "economia_reducao_volume": round(
                sum(float(r.get("economia_reducao_volume") or 0) for r in rows), 2
            ),
            "delta_volume": round(float(latest.get("delta_volume") or 0), 4),
        }

    def _breakdown_from_rows(self, rows: list[dict]) -> dict[str, float]:
        keys = (
            "economia_tempo",
            "economia_retrabalho",
            "economia_erros",
            "economia_outros",
            "economia_recursos_compartilhados",
        )
        if not rows:
            return {key: 0.0 for key in keys}
        return {
            key: round(sum(float(r.get(key) or 0) for r in rows), 2) for key in keys
        }

    @staticmethod
    def _volume_avisos(
        *,
        categoria: str,
        volume_acima: bool,
        volume_abaixo: bool,
        delta_volume: float,
    ) -> list[dict[str, Any]]:
        avisos: list[dict[str, Any]] = []
        cat = (categoria or "economia_tempo").strip().lower()
        if volume_acima:
            avisos.append(
                {
                    "code": "volume_acima_referencia",
                    "severity": "capacidade",
                    "delta_volume": delta_volume,
                    "message": (
                        "Volume acima da referência — há ganho de capacidade "
                        "incluído na economia bruta e no ROI, além da economia de custo unitário."
                    ),
                }
            )
        if volume_abaixo:
            avisos.append(
                {
                    "code": "volume_abaixo_referencia",
                    "severity": "reducao_volume",
                    "delta_volume": delta_volume,
                    "message": (
                        "Volume abaixo da referência — parte da economia vem de "
                        "menos execuções, não só de menos tempo por execução."
                    ),
                }
            )
        if cat == "economia_tempo" and (volume_acima or volume_abaixo):
            avisos.append(
                {
                    "code": "economia_tempo_volume_diverge",
                    "severity": "cadastro",
                    "delta_volume": delta_volume,
                    "message": (
                        "Categoria «Economia de tempo»: volumes diferentes misturam "
                        "Δtempo com Δvolume. Para comparação 1:1, alinhe o volume à referência."
                    ),
                }
            )
        return avisos
