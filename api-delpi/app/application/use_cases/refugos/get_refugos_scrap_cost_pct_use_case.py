from __future__ import annotations

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.refugos.refugos_formatters import as_int, round_cost, round_qty
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


class GetRefugosScrapCostPctUseCase:
    """Scrap cost (SBC) over financial ROL for the same branch scope and period."""

    def __init__(
        self,
        refugos_repository: RefugosRepositoryPort,
        financial_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._refugos_repository = refugos_repository
        self._financial_repository = financial_repository

    def execute(self, request: RefugosQueryRequest) -> dict:
        date_start, date_end_exclusive = request.period.protheus_closed_open()
        day_start, day_end_exclusive = request.period.day_closed_open()
        month_start, month_end_exclusive = request.period.month_closed_open()
        start_iso, end_iso = request.period.iso_range()
        branch = request.period.filial
        branch_filter_applied = branch is not None
        consolidated = not branch_filter_applied

        row = self._refugos_repository.get_resumo(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            day_start=day_start,
            day_end_exclusive=day_end_exclusive,
            month_start=month_start,
            month_end_exclusive=month_end_exclusive,
            **request.filter_kwargs(),
        )

        rol_data = self._financial_repository.get_rol(
            GetRolRequest(
                branch=branch,
                start_date=start_iso,
                end_date=end_iso,
            )
        )

        scrap_cost = round_cost(row.get("total_valor"))
        rol_with_ipi = round_cost(rol_data.get("rol_with_ipi"))
        rol = round_cost(rol_data.get("rol"))
        scrap_cost_pct = (
            round((scrap_cost / rol_with_ipi) * 100, 4) if rol_with_ipi > 0 else None
        )

        return {
            "branch": branch or "consolidated",
            "start_date": start_iso,
            "end_date": end_iso,
            "scrap_cost": scrap_cost,
            "quantity": round_qty(row.get("total_quantidade")),
            "occurrences": as_int(row.get("ocorrencias")),
            "records_without_cost": as_int(row.get("registros_sem_custo")),
            "rol": rol,
            "rol_with_ipi": rol_with_ipi,
            "scrap_cost_pct": scrap_cost_pct,
            "filters_applied": {
                "mp": request.mp,
                "pa": request.pa,
                "op": request.op,
                "motivo": request.motivo,
                "recurso": request.recurso,
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
                "scrap_cost": scrap_cost,
                "rol_with_ipi": rol_with_ipi,
                "scrap_cost_pct": scrap_cost_pct,
                "is_complete": True,
            },
        }
