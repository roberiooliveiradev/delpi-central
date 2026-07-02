from __future__ import annotations

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_filtros_response import (
    DespesasCentroCustoFiltrosResponse,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)
from app.domain.ports.financeiro_despesas_centro_custo.despesas_centro_custo_repository_port import (
    DespesasCentroCustoRepositoryPort,
)


class GetDespesasCentroCustoFiltrosUseCase:
    def __init__(self, repository: DespesasCentroCustoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: DespesasCentroCustoQueryRequest,
    ) -> DespesasCentroCustoFiltrosResponse:
        start_date, end_date = request.resolve_protheus_period()
        payload = self._repository.get_filtros(
            start_date=start_date,
            end_date=end_date,
            branch=request.branch,
            cost_center=request.cost_center,
        )

        return DespesasCentroCustoFiltrosResponse(
            periodo={
                "data_inicio": start_date,
                "data_fim": end_date,
            },
            filiais=payload.get("filiais") or [],
            centros_custo=payload.get("centros_custo") or [],
            fornecedores=payload.get("fornecedores") or [],
        )
