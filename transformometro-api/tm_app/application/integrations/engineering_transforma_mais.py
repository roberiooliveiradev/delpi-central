from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tm_app.application.services.dashboard_recalc_service import _normalize_competencia_bound
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
    DashboardDataRepository,
)


@dataclass(frozen=True)
class EngineeringProcessFilters:
    id: str | None = None
    name_process: str | None = None
    filial_id: str | None = None
    sector_name: str | None = None
    status: str | None = None


class EngineeringTransformaMaisService:
    """Contrato legado (api-delpi / SI / dashboard-engineering) sobre cache ou calculador oficial."""

    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()
        self._cache = DashboardCalculoRepository()

    def list_processes(self, filters: EngineeringProcessFilters) -> dict[str, Any]:
        if self._cache.count() > 0:
            rows = self._cache.query_instancias_operacionais(filial_id=filters.filial_id)
            mapped = [_map_process_row_from_cache(row) for row in rows]
        else:
            raw = DashboardDataRepository().load_raw()
            items = self._calculator.build_instancia_list(raw)
            mapped = [_map_process_row(row) for row in items]
        filtered = _apply_process_filters(mapped, filters)
        return {"total": len(filtered), "items": filtered}

    def get_summary(
        self,
        *,
        filial_id: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        if self._cache.count() > 0:
            summary = self._build_summary_from_cache(
                filial_id=filial_id,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            raw = DashboardDataRepository().load_raw()
            summary = self._calculator.build_summary(
                raw,
                filial_id=filial_id,
                start_date=start_date,
                end_date=end_date,
            )
        return _map_summary(summary)

    def _build_summary_from_cache(
        self,
        *,
        filial_id: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        competencia_inicio = _normalize_competencia_bound(start_date)
        competencia_fim = _normalize_competencia_bound(end_date)
        resumo = self._cache.query_resumo(
            filial_id=filial_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        evolucao = self._cache.query_evolucao(
            filial_id=filial_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        investimento_total = float(resumo.get("investimento_total") or 0)
        economia_liquida_total = float(resumo.get("economia_liquida_total") or 0)
        roi_medio = (
            economia_liquida_total / investimento_total if investimento_total > 0 else 0.0
        )

        period_comp_inicio = competencia_inicio or (
            evolucao[0].get("competencia") if evolucao else None
        )
        period_comp_fim = competencia_fim or (
            evolucao[-1].get("competencia") if evolucao else None
        )

        return {
            "solucoes_implementadas": int(resumo.get("solucoes_implementadas") or 0),
            "economia_liquida_total": economia_liquida_total,
            "economia_bruta_total": float(resumo.get("economia_bruta_total") or 0),
            "horas_economizadas_total": float(resumo.get("horas_economizadas_total") or 0),
            "roi_medio": self._calculator._round_final(roi_medio),
            "evolucao_mensal": evolucao,
            "periodo": {
                "competencia_inicio": period_comp_inicio,
                "competencia_fim": period_comp_fim,
                "economia_liquida_acumulada": economia_liquida_total,
            },
        }


def _map_process_row(row: dict) -> dict:
    implantacao = row.get("data_implantacao")
    if hasattr(implantacao, "isoformat"):
        implantacao = implantacao.isoformat()

    instancia_id = row.get("instancia_id") or row.get("processo_id")
    processo_id = row.get("processo_id")

    return {
        "id": instancia_id,
        "processo_id": processo_id,
        "instancia_id": instancia_id,
        "codigo_processo": row.get("codigo_processo"),
        "name_process": row.get("nome_processo") or "",
        "filial_id": row.get("filial_id"),
        "sector_name": row.get("setor_id"),
        "daily_savings": row.get("economia_diaria"),
        "payback_months": row.get("payback_meses"),
        "status": row.get("status_processo"),
        "implementetion_date": implantacao,
    }


def _map_process_row_from_cache(row: dict) -> dict:
    implantacao = row.get("data_implantacao")
    if hasattr(implantacao, "isoformat"):
        implantacao = implantacao.isoformat()

    return {
        "id": row.get("instancia_id"),
        "processo_id": row.get("processo_id"),
        "instancia_id": row.get("instancia_id"),
        "codigo_processo": row.get("codigo_processo"),
        "name_process": row.get("nome_processo") or "",
        "filial_id": row.get("filial_id"),
        "sector_name": row.get("setor_id"),
        "daily_savings": row.get("economia_diaria"),
        "payback_months": row.get("payback_meses"),
        "status": row.get("status_processo"),
        "implementetion_date": implantacao,
    }


def _map_summary(summary: dict) -> dict:
    monthly = [
        {
            "month": item.get("competencia"),
            "gross_savings_month": item.get("economia_bruta", 0),
            "gross_costs_month": 0.0,
            "gross_investment_month": item.get("investimento_unico_mes", 0),
            "gross_recurring_investment_month": item.get("custo_recorrente_mes", 0),
            "shared_resource_cost_month": item.get("custo_recursos_compartilhados_mes", 0),
            "investment_total_month": item.get("investimento_total_mes", 0),
            "net_savings_month": item.get("economia_liquida_mes", 0),
        }
        for item in summary.get("evolucao_mensal") or []
    ]

    periodo = summary.get("periodo") or {}
    range_summary = {
        "start_date": periodo.get("competencia_inicio"),
        "end_date": periodo.get("competencia_fim"),
        "accumulated_net_savings_until_now": periodo.get("economia_liquida_acumulada", 0),
    }

    return {
        "implemented_solutions_count": int(summary.get("solucoes_implementadas") or 0),
        "total_net_savings_until_now": float(summary.get("economia_liquida_total") or 0),
        "total_hours_saved_until_now": float(summary.get("horas_economizadas_total") or 0),
        "total_gross_costs_until_now": 0.0,
        "total_gross_savings_in_period": float(summary.get("economia_bruta_total") or 0),
        "average_roi": float(summary.get("roi_medio") or 0),
        "monthly_breakdown": monthly,
        "range_summary": range_summary,
    }


def _apply_process_filters(
    items: list[dict],
    filters: EngineeringProcessFilters,
) -> list[dict]:
    result = items

    if filters.id:
        needle = filters.id.lower()
        result = [
            i
            for i in result
            if needle in str(i.get("id") or "").lower()
            or needle in str(i.get("processo_id") or "").lower()
            or needle in str(i.get("instancia_id") or "").lower()
            or needle in str(i.get("codigo_processo") or "").lower()
        ]

    if filters.name_process:
        needle = filters.name_process.lower()
        result = [i for i in result if needle in str(i.get("name_process") or "").lower()]

    if filters.filial_id:
        needle = filters.filial_id.lower()
        result = [i for i in result if needle in str(i.get("filial_id") or "").lower()]

    if filters.sector_name:
        needle = filters.sector_name.lower()
        result = [i for i in result if needle in str(i.get("sector_name") or "").lower()]

    if filters.status:
        needle = filters.status.lower()
        result = [i for i in result if needle in str(i.get("status") or "").lower()]

    return result
