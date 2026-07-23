from __future__ import annotations

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.retrabalho.retrabalho_formatters import as_int, round_cost, round_hours
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


class GetRetrabalhoReworkCostPctUseCase:
    """Rework cost (RT view) over financial ROL for the same branch scope and period."""

    def __init__(
        self,
        retrabalho_repository: RetrabalhoRepositoryPort,
        financial_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._retrabalho_repository = retrabalho_repository
        self._financial_repository = financial_repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_iso, end_iso = request.period.iso_range()
        branch = request.period.filial
        branch_filter_applied = branch is not None
        consolidated = not branch_filter_applied
        common = {
            "start_date": start_iso,
            "end_date": end_iso,
            "branch": branch,
            "recurso": request.recurso,
            "centro_custo": request.centro_custo,
            "codigo_operador": request.codigo_operador,
        }

        row = self._retrabalho_repository.get_resumo(**common)
        rol_data = self._financial_repository.get_rol(
            GetRolRequest(
                branch=branch,
                start_date=start_iso,
                end_date=end_iso,
            )
        )

        rework_cost = round_cost(row.get("total_custo"))
        total_hours = round_hours(row.get("total_horas"))
        rol_with_ipi = round_cost(rol_data.get("rol_with_ipi"))
        rol = round_cost(rol_data.get("rol"))
        rework_cost_pct = (
            round((rework_cost / rol_with_ipi) * 100, 4) if rol_with_ipi > 0 else None
        )
        average_cost_per_hour = (
            round(rework_cost / total_hours, 2) if total_hours > 0 else 0.0
        )

        return {
            "branch": branch or "consolidated",
            "start_date": start_iso,
            "end_date": end_iso,
            "rework_cost": rework_cost,
            "total_hours": total_hours,
            "appointment_count": as_int(row.get("total_apontamentos")),
            "average_cost_per_hour": average_cost_per_hour,
            "records_without_cost": as_int(row.get("registros_sem_custo")),
            "rol": rol,
            "rol_with_ipi": rol_with_ipi,
            "rework_cost_pct": rework_cost_pct,
            "filters_applied": {
                "recurso": request.recurso,
                "centro_custo": request.centro_custo,
                "codigo_operador": request.codigo_operador,
            },
            "financial_context": {
                "gross_revenue": round_cost(rol_data.get("gross_revenue")),
                "returns": round_cost(rol_data.get("returns")),
                "discounts": round_cost(rol_data.get("discounts")),
                "rol": rol,
                "rol_with_ipi": rol_with_ipi,
                "ipi_separated": round_cost(rol_data.get("ipi_separated")),
            },
            "summary": {
                "branch": branch,
                "branch_filter_applied": branch_filter_applied,
                "consolidated_across_branches": consolidated,
                "period": {"start": start_iso, "end": end_iso},
                "rework_cost": rework_cost,
                "rol_with_ipi": rol_with_ipi,
                "rework_cost_pct": rework_cost_pct,
                "is_complete": True,
            },
        }
