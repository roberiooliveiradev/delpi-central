from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date
from typing import Any

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

    def load_filtered_raw(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
    ) -> TransformometroRawData:
        raw = self._data_repo.load_raw()
        return self._calculator.filter_raw(
            raw,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )

    def calculation_rows(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        filtered = self.load_filtered_raw(
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
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        raw = self._data_repo.load_raw()
        filtered = self._calculator.filter_raw(raw, filial_id=filial_id, setor_id=setor_id)
        summary = self._calculator.build_summary(
            filtered,
            filial_id=None,
            start_date=competencia_inicio,
            end_date=competencia_fim,
        )
        summary["fonte"] = "cadastro_tempo_real"
        return summary

    def query_evolucao(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        summary = self.build_summary(
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        return list(summary.get("evolucao_mensal") or [])

    def query_ranking_processos(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
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

        raw = self.load_filtered_raw(filial_id=filial_id, setor_id=setor_id)
        processos_by_id = {
            str(p.get("processo_id")): p for p in raw.processos if p.get("processo_id")
        }
        context = self._calculator._build_context(raw)
        implementation_review_by_process = {
            pid: self._calculator._pick_first_non_baseline_review(revisoes)
            for pid, revisoes in context.revisoes_by_processo.items()
        }

        by_processo: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "economia_liquida_mes": 0.0,
                "economia_bruta": 0.0,
                "competencias": set(),
            }
        )

        for row in target_rows:
            pid = str(row.get("processo_id") or "")
            if not pid:
                continue
            implementation_review = implementation_review_by_process.get(pid)
            if not implementation_review:
                continue
            implementation_date = self._calculator._review_implementation_date(
                implementation_review
            )
            if has_period_filter and not self._is_date_in_filter_period(
                implementation_date,
                competencia_inicio,
                competencia_fim,
            ):
                continue
            bucket = by_processo[pid]
            bucket["economia_liquida_mes"] += float(row.get("economia_liquida_mes") or 0)
            bucket["economia_bruta"] += float(row.get("economia_bruta") or 0)
            bucket["competencias"].add(str(row.get("competencia") or ""))

        ranking: list[dict[str, Any]] = []
        for pid, totals in by_processo.items():
            proc = processos_by_id.get(pid, {})
            implementation_review = implementation_review_by_process.get(pid)
            implementation_date = self._calculator._review_implementation_date(
                implementation_review
            )
            liquida = totals["economia_liquida_mes"]
            month_count = max(len(totals["competencias"]), 1)
            ranking.append(
                {
                    "processo_id": pid,
                    "codigo_processo": proc.get("codigo_processo"),
                    "nome_processo": proc.get("nome_processo"),
                    "filial_id": proc.get("filial_id"),
                    "setor_id": proc.get("setor_id"),
                    "economia_liquida_mes": round(liquida, 2),
                    "economia_bruta": round(totals["economia_bruta"], 2),
                    "economia_diaria": round(liquida / (30.0 * month_count), 2),
                    "competencia": (
                        max(totals["competencias"])
                        if totals["competencias"]
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

        ranking.sort(key=lambda item: float(item.get("economia_liquida_mes") or 0), reverse=True)
        return ranking[:limit]

    def _is_date_in_filter_period(
        self,
        value: date | None,
        competencia_inicio: str | None,
        competencia_fim: str | None,
    ) -> bool:
        if value is None:
            return False

        start_date = (
            self._calculator._parse_date(competencia_inicio)
            if competencia_inicio
            else None
        )
        end_date = self._calculator._parse_date(competencia_fim) if competencia_fim else None

        if end_date and competencia_fim and len(competencia_fim.strip()) <= 7:
            end_date = end_date.replace(
                day=calendar.monthrange(end_date.year, end_date.month)[1]
            )

        if start_date and value < start_date:
            return False
        if end_date and value > end_date:
            return False
        return True

    def query_resumo_por_familia(
        self,
        *,
        filial_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            filial_id=filial_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(filial_id=filial_id)
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
            bucket["economia_bruta"] += float(row.get("economia_bruta") or 0)
            bucket["economia_liquida_mes"] += float(row.get("economia_liquida_mes") or 0)

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
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(
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
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.calculation_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        raw = self.load_filtered_raw(
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
                    "filial_id": row.get("filial_id") or proc.get("filial_id"),
                    "setor_id": row.get("setor_id") or proc.get("setor_id"),
                    "competencia": row.get("competencia"),
                    "cenario_tipo": row.get("cenario_tipo"),
                    "economia_bruta": row.get("economia_bruta"),
                    "economia_liquida_mes": row.get("economia_liquida_mes"),
                    "investimento_unico_mes": row.get("investimento_unico_mes"),
                    "custo_recorrente_mes": row.get("custo_recorrente_mes"),
                    "horas_economizadas_mes": row.get("horas_economizadas_mes"),
                }
            )
        return export_rows

    def list_processos_calculados(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
    ) -> list[dict[str, Any]]:
        raw = self.load_filtered_raw(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
        )
        items = self._calculator.build_process_list(raw)
        for item in items:
            item["fonte"] = "cadastro_tempo_real"
        return items
