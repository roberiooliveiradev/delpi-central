from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_formatters import (
    as_int,
    display_operador_nome,
    round_cost,
    round_hours,
)
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


def _map_ranking_recurso(row: dict) -> dict:
    return {
        "recurso": row.get("recurso") or "",
        "centroCusto": row.get("centro_custo") or "",
        "totalApontamentos": as_int(row.get("total_apontamentos")),
        "totalHoras": round_hours(row.get("total_horas")),
        "totalCusto": round_cost(row.get("total_custo")),
        "horasSemCusto": round_hours(row.get("horas_sem_custo")),
    }


class GetRetrabalhoRecursosUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_date, end_date = request.period.iso_range()
        rows = self._repository.get_ranking_recursos(
            start_date=start_date,
            end_date=end_date,
            branch=request.period.filial,
            recurso=request.recurso,
            centro_custo=request.centro_custo,
            codigo_operador=request.codigo_operador,
            order_by=request.order_by,
            limit=request.resolve_ranking_limit(),
        )

        return {
            "periodo": request.periodo_dict(),
            "orderBy": request.order_by,
            "items": [_map_ranking_recurso(row) for row in rows],
        }


class GetRetrabalhoColaboradoresUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_date, end_date = request.period.iso_range()
        rows = self._repository.get_ranking_colaboradores(
            start_date=start_date,
            end_date=end_date,
            branch=request.period.filial,
            recurso=request.recurso,
            centro_custo=request.centro_custo,
            codigo_operador=request.codigo_operador,
            order_by=request.order_by,
            limit=request.resolve_ranking_limit(),
        )

        items = [
            {
                "codigoOperador": row.get("codigo_operador") or "",
                "nomeOperador": display_operador_nome(row.get("nome_operador")),
                "totalApontamentos": as_int(row.get("total_apontamentos")),
                "totalHoras": round_hours(row.get("total_horas")),
                "totalCusto": round_cost(row.get("total_custo")),
                "horasSemCusto": round_hours(row.get("horas_sem_custo")),
            }
            for row in rows
        ]

        return {
            "periodo": request.periodo_dict(),
            "orderBy": request.order_by,
            "items": items,
        }
