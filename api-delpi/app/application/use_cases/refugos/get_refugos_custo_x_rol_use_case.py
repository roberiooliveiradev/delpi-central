from __future__ import annotations

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.refugos.refugos_formatters import as_int, round_cost, round_qty
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


class GetRefugosCustoXRolUseCase:
    """Combina custo de refugo (SBC) com ROL financeiro do mesmo período/filial."""

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

        row = self._refugos_repository.get_resumo(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.period.filial,
            day_start=day_start,
            day_end_exclusive=day_end_exclusive,
            month_start=month_start,
            month_end_exclusive=month_end_exclusive,
            **request.filter_kwargs(),
        )

        rol_data = self._financial_repository.get_rol(
            GetRolRequest(
                branch=request.period.filial,
                start_date=start_iso,
                end_date=end_iso,
            )
        )

        custo_refugo = round_cost(row.get("total_valor"))
        rol_with_ipi = round_cost(rol_data.get("rol_with_ipi"))
        rol = round_cost(rol_data.get("rol"))
        custo_sobre_rol_pct = (
            round((custo_refugo / rol_with_ipi) * 100, 4) if rol_with_ipi > 0 else None
        )

        return {
            "periodo": request.periodo_dict(),
            "custoRefugo": custo_refugo,
            "totalQuantidade": round_qty(row.get("total_quantidade")),
            "ocorrencias": as_int(row.get("ocorrencias")),
            "registrosSemCusto": as_int(row.get("registros_sem_custo")),
            "rol": rol,
            "rolWithIpi": rol_with_ipi,
            "custoSobreRolPct": custo_sobre_rol_pct,
            "filtrosAplicados": {
                "mp": request.mp,
                "pa": request.pa,
                "op": request.op,
                "motivo": request.motivo,
                "recurso": request.recurso,
            },
            "financialContext": {
                "grossRevenue": round_cost(rol_data.get("gross_revenue")),
                "returns": round_cost(rol_data.get("returns")),
                "discounts": round_cost(rol_data.get("discounts")),
                "rol": rol,
                "rolWithIpi": rol_with_ipi,
                "ipiSeparated": round_cost(rol_data.get("ipi_separated")),
            },
            "branchFilterApplied": True,
            "summary": {
                "branch": request.period.filial,
                "branch_filter_applied": True,
                "consolidated_across_branches": False,
                "period": {"start": start_iso, "end": end_iso},
                "custo_refugo": custo_refugo,
                "rol_with_ipi": rol_with_ipi,
                "custo_sobre_rol_pct": custo_sobre_rol_pct,
                "is_complete": True,
            },
        }
