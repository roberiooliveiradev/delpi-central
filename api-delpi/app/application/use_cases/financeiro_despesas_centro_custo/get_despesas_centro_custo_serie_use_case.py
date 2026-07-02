from __future__ import annotations

from typing import Any

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)
from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_serie_response import (
    DespesasCentroCustoSeriePoint,
    DespesasCentroCustoSerieResponse,
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


class GetDespesasCentroCustoSerieUseCase:
    def __init__(self, repository: DespesasCentroCustoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: DespesasCentroCustoQueryRequest,
    ) -> DespesasCentroCustoSerieResponse:
        start_date, end_date = request.resolve_protheus_period()
        rows = self._repository.get_serie(
            start_date=start_date,
            end_date=end_date,
            branch=request.branch,
            cost_center=request.cost_center,
            supplier_code=request.supplier_code,
            supplier_store=request.supplier_store,
        )

        # Retorna apenas meses com lançamentos no período (sem preenchimento de zeros).
        serie: list[DespesasCentroCustoSeriePoint] = []
        for row in rows:
            ano_mes = str(row.get("ano_mes") or "").strip()
            if len(ano_mes) != 6 or not ano_mes.isdigit():
                continue

            serie.append(
                DespesasCentroCustoSeriePoint(
                    ano_mes=ano_mes,
                    ano=int(ano_mes[:4]),
                    mes=int(ano_mes[4:6]),
                    valor_total=_as_float(row.get("valor_total")),
                    quantidade_lancamentos=_as_int(row.get("quantidade_lancamentos")),
                )
            )

        return DespesasCentroCustoSerieResponse(
            periodo=request.periodo_dict(),
            serie=serie,
        )
