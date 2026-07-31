from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_request import (
    DespesasCentroCustoLancamentosRequest,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_lancamentos_use_case import (
    GetDespesasCentroCustoLancamentosUseCase,
)


def test_lancamentos_pagination_includes_total_alias_and_is_complete() -> None:
    repository = MagicMock()
    repository.count_lancamentos.return_value = 120
    repository.list_lancamentos.return_value = []
    use_case = GetDespesasCentroCustoLancamentosUseCase(repository=repository)
    request = DespesasCentroCustoLancamentosRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
        page=1,
        page_size=50,
    )

    result = use_case.execute(request)
    pagination = result.pagination.to_dict()

    assert pagination["total_items"] == 120
    assert pagination["total"] == 120
    assert pagination["total_pages"] == 3
    assert pagination["has_next"] is True
    assert pagination["has_previous"] is False
    assert pagination["is_complete"] is False
