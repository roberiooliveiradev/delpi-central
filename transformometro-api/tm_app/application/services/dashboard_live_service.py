from __future__ import annotations

from collections import defaultdict
from typing import Any

from tm_app.application.services.dashboard_view_scope_service import (
    DashboardScopeFilters,
    DashboardViewScopeService,
)
from tm_app.domain import calc_rules
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)


class DashboardLiveService:
    """Consultas do dashboard calculadas em tempo real a partir do cadastro."""

    COMPARABLE_SCENARIOS = DashboardCalculatorService.COMPARABLE_SCENARIOS

    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()
        self._data_repo = DashboardDataRepository()
        self._scope = DashboardViewScopeService()

    def load_filtered_raw(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        scope: DashboardScopeFilters | None = None,
    ) -> TransformometroRawData:
        resolved = scope or self._scope.resolve(
            view=view, filial_id=filial_id, setor_id=setor_id
        )
        raw = self._data_repo.load_raw()
        return self._scope.filter_raw_preserving_resource_rateio(
            raw,
            resolved,
            self._calculator,
            familia_processo=familia_processo,
        )

    def calculation_rows(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        filtered = self.load_filtered_raw(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )
        context = self._calculator._build_context(filtered)
        _, rows = self._calculator._calculate_monthly_series(
            context=context,
            start_date=competencia_inicio,
            end_date=competencia_fim,
        )
        return rows

    def build_summary(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        scope = self._scope.resolve(view=view, filial_id=filial_id, setor_id=setor_id)
        filtered = self.load_filtered_raw(scope=scope)
        summary = self._calculator.build_summary(
            filtered,
            filial_id=None,
            start_date=competencia_inicio,
            end_date=competencia_fim,
        )
        summary["roi_medio"] = self._calculate_consolidated_roi(summary)
        summary["fonte"] = "cadastro_tempo_real"
        summary["scope"] = self._scope.scope_meta(scope)
        return summary

    @staticmethod
    def _calculate_consolidated_roi(summary: dict[str, Any]) -> float:
        """Calcula o ROI consolidado do recorte usando os totais do dashboard.

        Mantem a chave ``roi_medio`` por compatibilidade com o frontend, mas evita
        a media simples de percentuais por revisao, que distorce o indicador quando
        uma revisao pequena tem economia negativa.
        """
        total_net_savings = float(summary.get("economia_liquida_total") or 0)
        total_investment = float(summary.get("investimento_total") or 0)
        if total_investment <= 0:
            return 0.0
        return total_net_savings / total_investment

    def query_evolucao(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        summary = self.build_summary(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        return list(summary.get("evolucao_mensal") or [])

    def query_ranking_processos(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        if not rows:
            return []

        has_period_filter = bool(competencia_inicio or competencia_fim)

        if competencia:
            target_rows = [
                row for row in rows if str(row.get("competencia") or "") == competencia
            ]
        elif has_period_filter:
            target_rows = rows
        else:
            target_competencia = max(str(row.get("competencia") or "") for row in rows)
            target_rows = [
                row
                for row in rows
                if str(row.get("competencia") or "") == target_competencia
            ]

        if not target_rows:
            return []

        raw = self.load_filtered_raw(view=view, filial_id=filial_id, setor_id=setor_id)
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }
        context = self._calculator._build_context(raw)
        implementation_review_by_process = {
            pid: self._calculator._pick_first_non_baseline_review(revisoes)
            for pid, revisoes in context.revisoes_by_processo.items()
        }

        by_processo: dict[str, calc_rules.ProcessPeriodBucket] = defaultdict(
            calc_rules.ProcessPeriodBucket
        )

        for row in target_rows:
            pid = str(row.get("processo_id") or "")
            if not pid:
                continue
            implementation_review = implementation_review_by_process.get(pid)
            if not implementation_review:
                continue
            prorated = calc_rules.prorate_dashboard_row_for_period(
                row,
                start_date=competencia_inicio,
                end_date=competencia_fim,
            )
            if prorated is None:
                continue
            by_processo[pid].merge_prorated(
                prorated,
                str(row.get("competencia") or ""),
            )

        ranking: list[dict[str, Any]] = []
        for pid, bucket in by_processo.items():
            proc = processos_by_id.get(pid, {})
            implementation_review = implementation_review_by_process.get(pid)
            implementation_date = self._calculator._review_implementation_date(
                implementation_review
            )
            totals = bucket.as_totals_dict()
            daily = calc_rules.daily_averages_from_period_totals(
                totals,
                bucket.competencias,
                start_date=competencia_inicio,
                end_date=competencia_fim,
            )
            ranking.append(
                {
                    "processo_id": pid,
                    "codigo_processo": proc.get("codigo_processo"),
                    "nome_processo": proc.get("nome_processo"),
                    "filial_id": proc.get("filial_id"),
                    "setor_id": proc.get("setor_id"),
                    "economia_liquida_mes": round(totals["economia_liquida_mes"], 2),
                    "economia_bruta": round(totals["economia_bruta"], 2),
                    "investimento_unico_mes": round(totals["investimento_unico_mes"], 2),
                    "custo_recorrente_mes": round(totals["custo_recorrente_mes"], 2),
                    "custo_recursos_compartilhados_mes": round(
                        totals["custo_recursos_compartilhados_mes"], 2
                    ),
                    "investimento_total_mes": round(totals["investimento_total_mes"], 2),
                    "economia_diaria": daily["economia_diaria"],
                    "horas_diaria": daily["horas_diaria"],
                    "horas_economizadas_mes": round(totals["horas_economizadas_mes"], 2),
                    "competencia": (
                        max(bucket.competencias)
                        if bucket.competencias
                        else competencia
                    ),
                    "data_implantacao": implementation_date.isoformat()
                    if implementation_date
                    else None,
                    "revisao_implantacao_id": implementation_review.get("revisao_id")
                    if implementation_review
                    else None,
                }
            )

        ranking.sort(key=lambda item: float(item.get("economia_diaria") or 0), reverse=True)
        return ranking[:limit]

    def _calculate_rows_proration_factor(
        self,
        rows: list[dict[str, Any]],
        *,
        competencia_inicio: str | None,
        competencia_fim: str | None,
    ) -> float:
        if not competencia_inicio or not competencia_fim:
            return 1.0

        by_competencia: dict[str, dict[str, float | str]] = {}
        for row in rows:
            competencia = str(row.get("competencia") or "")
            if not competencia:
                continue
            bucket = by_competencia.setdefault(
                competencia,
                {
                    "competencia": competencia,
                    "economia_bruta": 0.0,
                    "investimento_unico_mes": 0.0,
                    "custo_recorrente_mes": 0.0,
                    "investimento_total_mes": 0.0,
                    "custo_recursos_compartilhados_mes": 0.0,
                    "economia_liquida_mes": 0.0,
                },
            )
            bucket["economia_bruta"] = float(bucket["economia_bruta"]) + float(row.get("economia_bruta") or 0)
            bucket["investimento_unico_mes"] = float(bucket["investimento_unico_mes"]) + float(row.get("investimento_unico_mes") or 0)
            bucket["custo_recorrente_mes"] = float(bucket["custo_recorrente_mes"]) + float(row.get("custo_recorrente_mes") or 0)
            bucket["investimento_total_mes"] = float(bucket["investimento_total_mes"]) + float(row.get("investimento_total_mes") or 0)
            bucket["custo_recursos_compartilhados_mes"] = float(bucket["custo_recursos_compartilhados_mes"]) + float(
                row.get("custo_recursos_compartilhados_mes") or 0
            )
            bucket["economia_liquida_mes"] = float(bucket["economia_liquida_mes"]) + float(row.get("economia_liquida_mes") or 0)

        monthly_breakdown = [by_competencia[key] for key in sorted(by_competencia)]
        return self._calculator._calculate_date_range_proration_factor(
            start_date=competencia_inicio,
            end_date=competencia_fim,
            monthly_breakdown=monthly_breakdown,
        )

    def query_resumo_por_familia(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            view=view,
            filial_id=filial_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(view=view, filial_id=filial_id)
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }

        by_familia: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "processos": set(),
                "economia_bruta": 0.0,
                "economia_liquida_mes": 0.0,
            }
        )

        for row in rows:
            pid = str(row.get("processo_id") or "")
            proc = processos_by_id.get(pid, {})
            familia = (proc.get("familia_processo") or "").strip()
            if not familia:
                continue
            bucket = by_familia[familia]
            bucket["processos"].add(pid)
            prorated = calc_rules.prorate_dashboard_row_for_period(
                row,
                start_date=competencia_inicio,
                end_date=competencia_fim,
            )
            if prorated is None:
                continue
            bucket["economia_bruta"] += prorated["economia_bruta"]
            bucket["economia_liquida_mes"] += prorated["economia_liquida_mes"]

        items = [
            {
                "familia_processo": familia,
                "processos": len(bucket["processos"]),
                "economia_bruta": round(bucket["economia_bruta"], 2),
                "economia_liquida_mes": round(bucket["economia_liquida_mes"], 2),
            }
            for familia, bucket in by_familia.items()
        ]
        items.sort(key=lambda item: float(item.get("economia_liquida_mes") or 0), reverse=True)
        return items

    def query_process_monthly_liquida(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }

        aggregated: dict[tuple[str, str], float] = defaultdict(float)
        for row in rows:
            if str(row.get("cenario_tipo") or "").lower() not in self.COMPARABLE_SCENARIOS:
                continue
            pid = str(row.get("processo_id") or "")
            comp = str(row.get("competencia") or "")
            if not pid or not comp:
                continue
            aggregated[(pid, comp)] += float(row.get("economia_liquida_mes") or 0)

        result: list[dict[str, Any]] = []
        for (pid, comp), liquida in sorted(aggregated.items()):
            proc = processos_by_id.get(pid, {})
            result.append(
                {
                    "processo_id": pid,
                    "codigo_processo": proc.get("codigo_processo"),
                    "nome_processo": proc.get("nome_processo"),
                    "filial_id": proc.get("filial_id"),
                    "setor_id": proc.get("setor_id"),
                    "familia_processo": proc.get("familia_processo"),
                    "agrupador_ferramenta": proc.get("agrupador_ferramenta"),
                    "competencia": comp,
                    "economia_liquida_mes": round(liquida, 2),
                }
            )
        return result

    def query_export_rows(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }

        export_rows: list[dict[str, Any]] = []
        for row in sorted(rows, key=lambda r: (str(r.get("competencia") or ""), str(r.get("processo_id") or ""))):
            pid = str(row.get("processo_id") or "")
            proc = processos_by_id.get(pid, {})
            export_rows.append(
                {
                    "codigo_processo": proc.get("codigo_processo"),
                    "nome_processo": proc.get("nome_processo"),
                    "familia_processo": proc.get("familia_processo"),
                    "agrupador_ferramenta": proc.get("agrupador_ferramenta"),
                    "filial_id": row.get("codigo_filial") or proc.get("filial_id"),
                    "setor_id": row.get("codigo_setor") or proc.get("setor_id"),
                    "competencia": row.get("competencia"),
                    "cenario_tipo": row.get("cenario_tipo"),
                    "economia_bruta": row.get("economia_bruta"),
                    "economia_liquida_mes": row.get("economia_liquida_mes"),
                    "investimento_unico_mes": row.get("investimento_unico_mes"),
                    "custo_recorrente_mes": row.get("custo_recorrente_mes"),
                    "custo_recursos_compartilhados_mes": row.get(
                        "custo_recursos_compartilhados_mes"
                    ),
                    "investimento_total_mes": row.get("investimento_total_mes"),
                    "horas_economizadas_mes": row.get("horas_economizadas_mes"),
                }
            )
        return export_rows

    def list_processos_calculados(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
    ) -> list[dict[str, Any]]:
        raw = self.load_filtered_raw(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )
        items = self._calculator.build_process_list(raw)
        for item in items:
            item["fonte"] = "cadastro_tempo_real"
        return items
