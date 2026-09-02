from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.financeiro_despesas_centro_custo.despesas_centro_custo_lancamentos_request import (
    DespesasCentroCustoLancamentosRequest,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_lancamentos_use_case import (
    GetDespesasCentroCustoLancamentosUseCase,
)


def test_lancamentos_sem_busca_usa_resumo_e_nao_chama_count() -> None:
    repository = MagicMock()
    repository.get_resumo.return_value = {"quantidade_lancamentos": 120}
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

    repository.get_resumo.assert_called_once()
    repository.count_lancamentos.assert_not_called()
    assert pagination["total_items"] == 120
    assert pagination["total"] == 120
    assert pagination["total_pages"] == 3
    assert pagination["has_next"] is True
    assert pagination["has_previous"] is False
    assert pagination["is_complete"] is False


def test_lancamentos_com_busca_usa_overfetch_sem_count() -> None:
    repository = MagicMock()
    repository.list_lancamentos.return_value = [{"recno_sd1": i} for i in range(51)]
    use_case = GetDespesasCentroCustoLancamentosUseCase(repository=repository)
    request = DespesasCentroCustoLancamentosRequest.from_query(
        start_date="2025-06-01",
        end_date="2025-06-30",
        page=1,
        page_size=50,
        search="frete",
    )

    result = use_case.execute(request)

    repository.count_lancamentos.assert_not_called()
    repository.get_resumo.assert_not_called()
    list_kwargs = repository.list_lancamentos.call_args.kwargs
    assert list_kwargs["page_size"] == 51
    assert list_kwargs["search"] == "frete"
    assert len(result.items) == 50
    assert result.pagination.has_next is True
    assert result.pagination.is_complete is False
