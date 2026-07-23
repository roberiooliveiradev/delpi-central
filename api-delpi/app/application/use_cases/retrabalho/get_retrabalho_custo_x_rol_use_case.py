from __future__ import annotations

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.retrabalho.retrabalho_formatters import as_int, round_cost, round_hours
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


class GetRetrabalhoCustoXRolUseCase:
    """Combina custo de retrabalho (view RT) com ROL financeiro do mesmo período/filial."""

    def __init__(
        self,
        retrabalho_repository: RetrabalhoRepositoryPort,
        financial_repository: FinancialQueryRepositoryPort,
    ) -> None:
        self._retrabalho_repository = retrabalho_repository
        self._financial_repository = financial_repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_iso, end_iso = request.period.iso_range()
        common = {
            "start_date": start_iso,
            "end_date": end_iso,
            "branch": request.period.filial,
            "recurso": request.recurso,
            "centro_custo": request.centro_custo,
            "codigo_operador": request.codigo_operador,
        }

        row = self._retrabalho_repository.get_resumo(**common)
        rol_data = self._financial_repository.get_rol(
            GetRolRequest(
                branch=request.period.filial,
                start_date=start_iso,
                end_date=end_iso,
            )
        )

        custo_retrabalho = round_cost(row.get("total_custo"))
        total_horas = round_hours(row.get("total_horas"))
        rol_with_ipi = round_cost(rol_data.get("rol_with_ipi"))
        rol = round_cost(rol_data.get("rol"))
        custo_sobre_rol_pct = (
            round((custo_retrabalho / rol_with_ipi) * 100, 4)
            if rol_with_ipi > 0
            else None
        )
        custo_medio_hora = (
            round(custo_retrabalho / total_horas, 2) if total_horas > 0 else 0.0
        )

        return {
            "periodo": request.periodo_dict(),
            "custoRetrabalho": custo_retrabalho,
            "totalHoras": total_horas,
            "totalApontamentos": as_int(row.get("total_apontamentos")),
            "custoMedioHora": custo_medio_hora,
            "registrosSemCusto": as_int(row.get("registros_sem_custo")),
            "rol": rol,
            "rolWithIpi": rol_with_ipi,
            "custoSobreRolPct": custo_sobre_rol_pct,
            "filtrosAplicados": {
                "recurso": request.recurso,
                "centroCusto": request.centro_custo,
                "codigoOperador": request.codigo_operador,
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
                "custo_retrabalho": custo_retrabalho,
                "rol_with_ipi": rol_with_ipi,
                "custo_sobre_rol_pct": custo_sobre_rol_pct,
                "is_complete": True,
            },
        }
