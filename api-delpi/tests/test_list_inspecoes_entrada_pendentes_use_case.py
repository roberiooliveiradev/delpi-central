from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_pendentes_use_case import (
    ListInspecoesEntradaPendentesUseCase,
)


def test_list_inspecoes_entrada_pendentes_normalizes_items_and_pagination() -> None:
    repository = MagicMock()
    repository.count_pendentes_by_branch.return_value = 6
    repository.list_pendentes_by_branch.return_value = [
        {
            "Filial": "01",
            "Data_Recebimento": "20260617",
            "Hora_Recebimento": "17:11",
            "Nota_Fiscal": "000191170",
            "Codigo_Fornecedor": "000180",
            "Loja_Fornecedor": "01",
            "Nome_Fornecedor": "CRIMPER DO BRASIL IND.E COM. DE TERM E C",
            "Codigo_Produto": "10080026",
            "Descricao_Produto": "TERMINAL COMPRESSAO",
            "Quantidade": 4000,
            "Unidade_Medida": "PC",
            "Codigo_Situacao": "",
            "Status_Inspecao": "NAO_IDENTIFICADA",
        }
    ]

    use_case = ListInspecoesEntradaPendentesUseCase(repository)
    result = use_case.execute(branch="01", page=1, page_size=10)

    repository.count_pendentes_by_branch.assert_called_once_with("01")
    repository.list_pendentes_by_branch.assert_called_once_with(
        "01",
        page=1,
        page_size=10,
    )

    payload = result.to_dict()
    assert payload["branch"] == "01"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["received_date"] == "2026-06-17"
    assert payload["items"][0]["received_time"] == "17:11"
    assert payload["items"][0]["invoice_number"] == "000191170"
    assert payload["items"][0]["product_description"] == "TERMINAL COMPRESSAO"
    assert payload["items"][0]["quantity"] == 4000.0
    assert payload["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total": 6,
        "total_pages": 1,
    }


def test_list_inspecoes_entrada_pendentes_returns_empty_list_when_no_rows() -> None:
    repository = MagicMock()
    repository.count_pendentes_by_branch.return_value = 0
    repository.list_pendentes_by_branch.return_value = []

    use_case = ListInspecoesEntradaPendentesUseCase(repository)
    result = use_case.execute(branch="02", page=1, page_size=50)

    payload = result.to_dict()
    assert payload["items"] == []
    assert payload["pagination"]["total"] == 0
    assert payload["pagination"]["total_pages"] == 1


def test_list_inspecoes_entrada_pendentes_clamps_page_size() -> None:
    repository = MagicMock()
    repository.count_pendentes_by_branch.return_value = 0
    repository.list_pendentes_by_branch.return_value = []

    use_case = ListInspecoesEntradaPendentesUseCase(repository)
    use_case.execute(branch="01", page=0, page_size=500)

    repository.list_pendentes_by_branch.assert_called_once_with(
        "01",
        page=1,
        page_size=200,
    )


def test_list_inspecoes_entrada_pendentes_parses_comma_decimal_quantity() -> None:
    repository = MagicMock()
    repository.count_pendentes_by_branch.return_value = 1
    repository.list_pendentes_by_branch.return_value = [
        {
            "Filial": "02",
            "Data_Recebimento": "20260617",
            "Hora_Recebimento": "12:28",
            "Nota_Fiscal": "001004051",
            "Codigo_Fornecedor": "000002",
            "Loja_Fornecedor": "01",
            "Nome_Fornecedor": "TE CONNECTIVITY BRASIL IND DE ELET LTDA",
            "Codigo_Produto": "10090023",
            "Quantidade": "46093,07",
            "Unidade_Medida": "PC",
            "Codigo_Situacao": "",
            "Status_Inspecao": "NAO_IDENTIFICADA",
        }
    ]

    use_case = ListInspecoesEntradaPendentesUseCase(repository)
    result = use_case.execute(branch="02", page=1, page_size=10)

    assert result.to_dict()["items"][0]["quantity"] == 46093.07


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_entrada_pendentes_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaPendentesUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.count_pendentes_by_branch.assert_not_called()
    repository.list_pendentes_by_branch.assert_not_called()
