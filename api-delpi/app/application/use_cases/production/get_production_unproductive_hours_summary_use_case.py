"""Use case — resumo de horas improdutivas."""

from __future__ import annotations

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursQueryRequest,
    as_int,
    display_operator_name,
    round_cost,
    round_hours,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)


class GetProductionUnproductiveHoursSummaryUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursQueryRequest) -> dict:
        common = request.filter_kwargs()
        row = self._repository.get_summary(**common)
        top_resource = self._repository.get_top_resource(**common)
        top_operator = self._repository.get_top_operator(**common)

        total_apontamentos = as_int(row.get("total_apontamentos"))
        total_horas = round_hours(row.get("total_horas"))
        total_custo = round_cost(row.get("total_custo"))
        registros_sem_custo = as_int(row.get("registros_sem_custo"))
        horas_sem_custo = round_hours(row.get("horas_sem_custo"))
        percentual_horas_sem_custo = (
            round((horas_sem_custo / total_horas) * 100, 2) if total_horas > 0 else 0.0
        )
        custo_medio_hora = (
            round(total_custo / total_horas, 2) if total_horas > 0 else 0.0
        )

        principal_recurso = None
        if top_resource and top_resource.get("recurso"):
            principal_recurso = {
                "recurso": top_resource.get("recurso") or "",
                "totalHoras": round_hours(top_resource.get("total_horas")),
            }

        principal_colaborador = None
        if top_operator and top_operator.get("codigo_operador"):
            principal_colaborador = {
                "codigoOperador": top_operator.get("codigo_operador") or "",
                "nomeOperador": display_operator_name(top_operator.get("nome_operador")),
                "totalHoras": round_hours(top_operator.get("total_horas")),
            }

        return {
            "periodo": request.periodo_dict(),
            "summary": {
                "totalApontamentos": total_apontamentos,
                "totalHoras": total_horas,
                "totalCusto": total_custo,
                "custoMedioHora": custo_medio_hora,
                "registrosSemCusto": registros_sem_custo,
                "horasSemCusto": horas_sem_custo,
                "percentualHorasSemCusto": percentual_horas_sem_custo,
                "principalRecursoPorHoras": principal_recurso,
                "principalColaboradorPorHoras": principal_colaborador,
            },
        }
