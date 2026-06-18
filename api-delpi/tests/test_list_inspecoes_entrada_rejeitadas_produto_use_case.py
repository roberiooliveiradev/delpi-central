from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_rejeitadas_produto_use_case import (
    ListInspecoesEntradaRejeitadasProdutoUseCase,
)


def test_list_inspecoes_entrada_rejeitadas_produto_normalizes_items_and_total() -> None:
    repository = MagicMock()
    repository.count_rejeitadas_by_branch.return_value = 2
    repository.list_rejeitadas_by_branch.return_value = [
        {
            "Filial": "02",
            "Id_Inspecao": "abc-123",
            "Data_Laudo": "20260617",
            "Hora_Laudo": "06:20",
            "Nota_Fiscal": "000042999",
            "Nome_Fornecedor": "FORNECEDOR TESTE LTDA",
            "Codigo_Produto": "10080026",
            "Descricao_Produto": "TERMINAL COMPRESSAO",
            "Lote": "LOTE001",
            "Quantidade": 1000,
            "Unidade_Medida": "PC",
        }
    ]

    use_case = ListInspecoesEntradaRejeitadasProdutoUseCase(repository)
    result = use_case.execute(branch="02", limit=50)

    repository.count_rejeitadas_by_branch.assert_called_once_with("02")
    repository.list_rejeitadas_by_branch.assert_called_once_with("02", limit=50)

    payload = result.to_dict()
    assert payload["branch"] == "02"
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["report_date"] == "2026-06-17"
    assert payload["items"][0]["product_description"] == "TERMINAL COMPRESSAO"
    assert payload["items"][0]["supplier_name"] == "FORNECEDOR TESTE LTDA"


def test_list_inspecoes_entrada_rejeitadas_produto_clamps_limit() -> None:
    repository = MagicMock()
    repository.count_rejeitadas_by_branch.return_value = 0
    repository.list_rejeitadas_by_branch.return_value = []

    use_case = ListInspecoesEntradaRejeitadasProdutoUseCase(repository)
    use_case.execute(branch="01", limit=500)

    repository.list_rejeitadas_by_branch.assert_called_once_with("01", limit=200)


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_entrada_rejeitadas_produto_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaRejeitadasProdutoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.count_rejeitadas_by_branch.assert_not_called()
    repository.list_rejeitadas_by_branch.assert_not_called()
