"""Use case — ranking de horas improdutivas por dimensão."""

from __future__ import annotations

from typing import Any

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursRankingRequest,
    as_int,
    clean_text,
    display_operator_name,
    round_cost,
    round_hours,
)
from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)
from app.domain.production.unproductive_hours_view_scope import (
    RANK_BY_COST_CENTER,
    RANK_BY_OPERATION,
    RANK_BY_OPERATOR,
    RANK_BY_PRODUCT,
    RANK_BY_RESOURCE,
    RANK_BY_STOP_REASON,
)


def _dimension_fields(rank_by: str, row: dict[str, Any]) -> dict[str, Any]:
    if rank_by == RANK_BY_STOP_REASON:
        return {
            "motivo": clean_text(row.get("motivo")),
            "motivoDescricao": clean_text(row.get("motivo_descricao")) or None,
        }
    if rank_by == RANK_BY_RESOURCE:
        return {
            "recurso": clean_text(row.get("recurso")),
            "centroCusto": clean_text(row.get("centro_custo")),
        }
    if rank_by == RANK_BY_COST_CENTER:
        return {"centroCusto": clean_text(row.get("centro_custo"))}
    if rank_by == RANK_BY_OPERATOR:
        return {
            "codigoOperador": clean_text(row.get("codigo_operador")),
            "nomeOperador": display_operator_name(row.get("nome_operador")),
        }
    if rank_by == RANK_BY_PRODUCT:
        return {"produto": clean_text(row.get("produto"))}
    if rank_by == RANK_BY_OPERATION:
        return {"operacao": clean_text(row.get("operacao"))}
    return {}


class GetProductionUnproductiveHoursRankingUseCase:
    def __init__(self, repository: UnproductiveHoursRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: UnproductiveHoursRankingRequest) -> dict:
        rows = self._repository.get_ranking(
            **request.filter_kwargs(),
            rank_by=request.rank_by,
            metric=request.metric,
            limit=request.limit,
        )
        items = []
        for index, row in enumerate(rows, start=1):
            item = {
                "rank": index,
                **_dimension_fields(request.rank_by, row),
                "totalApontamentos": as_int(row.get("total_apontamentos")),
                "totalHoras": round_hours(row.get("total_horas")),
                "totalCusto": round_cost(row.get("total_custo")),
                "horasSemCusto": round_hours(row.get("horas_sem_custo")),
            }
            items.append(item)
        return {
            "periodo": request.periodo_dict(),
            "rankBy": request.rank_by,
            "metric": request.metric,
            "limit": request.limit,
            "items": items,
        }
