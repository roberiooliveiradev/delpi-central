from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_resumo_response import (
    DespesasCentroCustoResumoResponse,
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


class GetDespesasCentroCustoResumoUseCase:
    def __init__(self, repository: DespesasCentroCustoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: DespesasCentroCustoQueryRequest,
    ) -> DespesasCentroCustoResumoResponse:
        start_date, end_date = request.resolve_protheus_period()
        row = self._repository.get_resumo(
            start_date=start_date,
            end_date=end_date,
            branch=request.branch,
            cost_center=request.cost_center,
            supplier_code=request.supplier_code,
            supplier_store=request.supplier_store,
        )

        total_periodo = _as_float(row.get("total_periodo"))
        quantidade_lancamentos = _as_int(row.get("quantidade_lancamentos"))
        ticket_medio = (
            round(total_periodo / quantidade_lancamentos, 2)
            if quantidade_lancamentos > 0
            else 0.0
        )

        return DespesasCentroCustoResumoResponse(
            periodo=request.periodo_dict(),
            total_periodo=total_periodo,
            quantidade_lancamentos=quantidade_lancamentos,
            quantidade_centros_custo=_as_int(row.get("quantidade_centros_custo")),
            quantidade_fornecedores=_as_int(row.get("quantidade_fornecedores")),
            ticket_medio=ticket_medio,
            maior_lancamento=_as_float(row.get("maior_lancamento")),
        )
