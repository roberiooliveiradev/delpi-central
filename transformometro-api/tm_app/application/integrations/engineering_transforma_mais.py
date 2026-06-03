from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
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
    """Contrato legado (api-delpi / SI / dashboard-engineering) sobre o calculador oficial."""

    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()

    def list_processes(self, filters: EngineeringProcessFilters) -> dict[str, Any]:
        raw = DashboardDataRepository().load_raw()
        items = self._calculator.build_process_list(raw)
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
        raw = DashboardDataRepository().load_raw()
        summary = self._calculator.build_summary(
            raw,
            filial_id=filial_id,
            start_date=start_date,
            end_date=end_date,
        )
        return _map_summary(summary)


def _map_process_row(row: dict) -> dict:
    implantacao = row.get("data_implantacao")
    if hasattr(implantacao, "isoformat"):
        implantacao = implantacao.isoformat()

    return {
        "id": row.get("processo_id"),
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
        result = [i for i in result if needle in str(i.get("id") or "").lower()]

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
