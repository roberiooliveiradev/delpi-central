from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_formatters import (
    as_int,
    display_operador_nome,
    round_cost,
    round_hours,
)
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


class GetRetrabalhoResumoUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_date, end_date = request.period.iso_range()
        common = {
            "start_date": start_date,
            "end_date": end_date,
            "branch": request.period.filial,
            "recurso": request.recurso,
            "centro_custo": request.centro_custo,
            "codigo_operador": request.codigo_operador,
        }

        row = self._repository.get_resumo(**common)
        top_recurso = self._repository.get_top_recurso(**common)
        top_colaborador = self._repository.get_top_colaborador(**common)

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
        if top_recurso and top_recurso.get("recurso"):
            principal_recurso = {
                "recurso": top_recurso.get("recurso") or "",
                "totalHoras": round_hours(top_recurso.get("total_horas")),
            }

        principal_colaborador = None
        if top_colaborador and top_colaborador.get("codigo_operador"):
            principal_colaborador = {
                "codigoOperador": top_colaborador.get("codigo_operador") or "",
                "nomeOperador": display_operador_nome(top_colaborador.get("nome_operador")),
                "totalHoras": round_hours(top_colaborador.get("total_horas")),
            }

        return {
            "periodo": request.periodo_dict(),
            "totalApontamentos": total_apontamentos,
            "totalHoras": total_horas,
            "totalCusto": total_custo,
            "custoMedioHora": custo_medio_hora,
            "registrosSemCusto": registros_sem_custo,
            "horasSemCusto": horas_sem_custo,
            "percentualHorasSemCusto": percentual_horas_sem_custo,
            "principalRecursoPorHoras": principal_recurso,
            "principalColaboradorPorHoras": principal_colaborador,
        }
