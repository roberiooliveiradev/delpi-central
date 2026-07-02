from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_query_request import (
    DespesasCentroCustoQueryRequest,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_resumo_use_case import (
    GetDespesasCentroCustoResumoUseCase,
)


def test_resumo_use_case_calculates_ticket_medio_and_zero_division() -> None:
    repository = MagicMock()
    repository.get_resumo.return_value = {
        "total_periodo": 1000,
        "quantidade_lancamentos": 4,
        "quantidade_centros_custo": 2,
        "quantidade_fornecedores": 3,
        "maior_lancamento": 500,
    }

    use_case = GetDespesasCentroCustoResumoUseCase(repository=repository)
    request = DespesasCentroCustoQueryRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
    )

    result = use_case.execute(request)
    assert result.ticket_medio == 250.0
    assert result.total_periodo == 1000.0

    repository.get_resumo.return_value = {
        "total_periodo": 0,
        "quantidade_lancamentos": 0,
        "quantidade_centros_custo": 0,
        "quantidade_fornecedores": 0,
        "maior_lancamento": 0,
    }
    empty_result = use_case.execute(request)
    assert empty_result.ticket_medio == 0.0
