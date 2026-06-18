from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_pendentes_fornecedor_use_case import (
    ListInspecoesEntradaPendentesFornecedorUseCase,
)


def test_list_inspecoes_entrada_pendentes_fornecedor_normalizes_items_and_totals() -> None:
    repository = MagicMock()
    repository.list_pendentes_fornecedor_by_branch.return_value = [
        {
            "Filial": "01",
            "Nome_Fornecedor": "CRIMPER DO BRASIL IND.E COM. DE TERM E C",
            "Qtde_Pendentes": 3,
        },
        {
            "Filial": "01",
            "Nome_Fornecedor": "TRAMAR INDUSTRIAL LTDA",
            "Qtde_Pendentes": 2,
        },
        {
            "Filial": "01",
            "Nome_Fornecedor": "RCM CABOS ELETRICOS LTDA",
            "Qtde_Pendentes": 1,
        },
    ]

    use_case = ListInspecoesEntradaPendentesFornecedorUseCase(repository)
    result = use_case.execute(branch="01")

    repository.list_pendentes_fornecedor_by_branch.assert_called_once_with("01")
    payload = result.to_dict()
    assert payload["branch"] == "01"
    assert payload["total_suppliers"] == 3
    assert payload["total_pending"] == 6
    assert payload["items"][0]["supplier_name"] == "CRIMPER DO BRASIL IND.E COM. DE TERM E C"
    assert payload["items"][0]["pending_count"] == 3


def test_list_inspecoes_entrada_pendentes_fornecedor_preserves_repository_order() -> None:
    repository = MagicMock()
    repository.list_pendentes_fornecedor_by_branch.return_value = [
        {"Filial": "02", "Nome_Fornecedor": "B", "Qtde_Pendentes": 10},
        {"Filial": "02", "Nome_Fornecedor": "A", "Qtde_Pendentes": 10},
        {"Filial": "02", "Nome_Fornecedor": "C", "Qtde_Pendentes": 5},
    ]

    use_case = ListInspecoesEntradaPendentesFornecedorUseCase(repository)
    result = use_case.execute(branch="02")

    names = [item["supplier_name"] for item in result.to_dict()["items"]]
    counts = [item["pending_count"] for item in result.to_dict()["items"]]
    assert counts == [10, 10, 5]
    assert names == ["B", "A", "C"]


def test_list_inspecoes_entrada_pendentes_fornecedor_returns_empty_when_no_rows() -> None:
    repository = MagicMock()
    repository.list_pendentes_fornecedor_by_branch.return_value = []

    use_case = ListInspecoesEntradaPendentesFornecedorUseCase(repository)
    result = use_case.execute(branch="02")

    payload = result.to_dict()
    assert payload["items"] == []
    assert payload["total_suppliers"] == 0
    assert payload["total_pending"] == 0


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_entrada_pendentes_fornecedor_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaPendentesFornecedorUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.list_pendentes_fornecedor_by_branch.assert_not_called()
