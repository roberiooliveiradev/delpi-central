from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_ranking_centros_response import (
    DespesasCentroCustoRankingCentroItem,
    DespesasCentroCustoRankingCentrosResponse,
)
from app.domain.ports.financeiro_despesas_centro_custo.despesas_centro_custo_repository_port import (
    DespesasCentroCustoRepositoryPort,
)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class GetDespesasCentroCustoRankingCentrosUseCase:
    def __init__(self, repository: DespesasCentroCustoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: DespesasCentroCustoQueryRequest,
    ) -> DespesasCentroCustoRankingCentrosResponse:
        start_date, end_date = request.resolve_protheus_period()
        limit = request.resolve_ranking_limit()
        rows = self._repository.get_ranking_centros(
            start_date=start_date,
            end_date=end_date,
            branch=request.branch,
            supplier_code=request.supplier_code,
            supplier_store=request.supplier_store,
            limit=limit,
        )

        ranking = [
            DespesasCentroCustoRankingCentroItem(
                centro_custo_codigo=_clean(row.get("centro_custo_codigo")),
                centro_custo_descricao=_clean(row.get("centro_custo_descricao")),
                valor_total=_as_float(row.get("valor_total")),
                quantidade_lancamentos=_as_int(row.get("quantidade_lancamentos")),
                percentual=_as_float(row.get("percentual")),
            )
            for row in rows
            if _clean(row.get("centro_custo_codigo"))
        ]

        return DespesasCentroCustoRankingCentrosResponse(
            periodo=request.periodo_dict(),
            ranking=ranking,
        )
