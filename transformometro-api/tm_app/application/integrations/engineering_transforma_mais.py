from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tm_app.application.services.dashboard_live_service import (
    DashboardLiveService,
    load_raw_cached,
)
from tm_app.application.services.dashboard_view_scope_service import count_active_filiais
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService


@dataclass(frozen=True)
class EngineeringProcessFilters:
    id: str | None = None
    name_process: str | None = None
    filial_id: str | None = None
    sector_name: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int = 200


class EngineeringTransformaMaisService:
    """Contrato legado (api-delpi / SI / dashboard-engineering) sobre o calculador oficial.

    Fonte única = motor live (mesmo cálculo do dashboard) sobre o cadastro, com
    ``DashboardQueryCache`` compartilhado. Sem dependência da tabela materializada:
    aceita faixas de tempo por dia (prorrata) e nunca fica obsoleto após CRUD.
    """

    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()

    def list_processes(self, filters: EngineeringProcessFilters) -> dict[str, Any]:
        """Lista processos no mesmo grão do dashboard Transformômetro (ranking por processo).

        Usa ``query_ranking_processos`` — economia diária prorrateada no recorte — em vez de
        uma linha por instância/melhoria, que duplicava nomes no gráfico de engenharia.
        """
        rows = DashboardLiveService().query_ranking_processos(
            filial_id=filters.filial_id,
            competencia_inicio=filters.start_date,
            competencia_fim=filters.end_date,
            limit=max(1, min(int(filters.limit or 200), 500)),
        )
        processos_by_id = {
            str(processo.get("processo_id")): processo
            for processo in load_raw_cached().processos
            if processo.get("processo_id")
        }
        mapped = [
            _map_ranking_row(
                row,
                processos_by_id.get(str(row.get("processo_id") or ""), {}),
            )
            for row in rows
        ]
        filtered = _apply_process_filters(mapped, filters)
        return {"total": len(filtered), "items": filtered}

    def get_summary(
        self,
        *,
        filial_id: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        raw = load_raw_cached()
        escopo_unidades = 1 if filial_id else count_active_filiais()
        summary = self._calculator.build_summary(
            raw,
            filial_id=filial_id,
            start_date=start_date,
            end_date=end_date,
            escopo_unidades=escopo_unidades,
        )
        return _map_summary(summary)


def _map_ranking_row(row: dict, process_row: dict) -> dict:
    processo_id = str(row.get("processo_id") or "")
    implantacao = row.get("data_implantacao")
    if hasattr(implantacao, "isoformat"):
        implantacao = implantacao.isoformat()

    return {
        "id": processo_id,
        "processo_id": processo_id,
        "instancia_id": processo_id,
        "codigo_processo": row.get("codigo_processo") or process_row.get("codigo_processo"),
        "name_process": row.get("nome_processo") or process_row.get("nome_processo") or "",
        "filial_id": row.get("filial_id") or process_row.get("filial_id"),
        "sector_name": row.get("setor_id") or process_row.get("setor_id"),
        "daily_savings": row.get("economia_diaria"),
        "payback_months": None,
        "status": process_row.get("status_processo"),
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
