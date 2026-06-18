from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_rejeitadas_ensaiador_use_case import (
    ListInspecoesEntradaRejeitadasEnsaiadorUseCase,
)


def test_list_inspecoes_entrada_rejeitadas_ensaiador_normalizes_items_and_totals() -> None:
    repository = MagicMock()
    repository.list_rejeitadas_ensaiador_by_branch.return_value = [
        {
            "Filial": "01",
            "Matricula_Ensaiador": "30006",
            "Nome_Ensaiador": "NATHALIA FERNANDES SALES",
            "Login_Ensaiador": "NATHALIA",
            "Qtde_Inspecoes_Rejeitadas": 1,
        }
    ]

    use_case = ListInspecoesEntradaRejeitadasEnsaiadorUseCase(repository)
    result = use_case.execute(branch="01")

    repository.list_rejeitadas_ensaiador_by_branch.assert_called_once_with("01")
    payload = result.to_dict()
    assert payload["branch"] == "01"
    assert payload["total_inspectors"] == 1
    assert payload["total_rejected"] == 1
    assert payload["items"][0] == {
        "branch": "01",
        "inspector_registration": "30006",
        "inspector_name": "NATHALIA FERNANDES SALES",
        "inspector_login": "NATHALIA",
        "rejected_inspections": 1,
    }


def test_list_inspecoes_entrada_rejeitadas_ensaiador_preserves_repository_order() -> None:
    repository = MagicMock()
    repository.list_rejeitadas_ensaiador_by_branch.return_value = [
        {
            "Filial": "02",
            "Matricula_Ensaiador": "20167",
            "Nome_Ensaiador": "PATRICIA ANDRE DA SILVA",
            "Login_Ensaiador": "PATRICIA.SILVA",
            "Qtde_Inspecoes_Rejeitadas": 2,
        },
        {
            "Filial": "02",
            "Matricula_Ensaiador": "20410",
            "Nome_Ensaiador": "YURI BARBEITO COSTA",
            "Login_Ensaiador": "YURI",
            "Qtde_Inspecoes_Rejeitadas": 2,
        },
    ]

    use_case = ListInspecoesEntradaRejeitadasEnsaiadorUseCase(repository)
    result = use_case.execute(branch="02")

    payload = result.to_dict()
    assert payload["total_inspectors"] == 2
    assert payload["total_rejected"] == 4
    assert [item["inspector_name"] for item in payload["items"]] == [
        "PATRICIA ANDRE DA SILVA",
        "YURI BARBEITO COSTA",
    ]
    assert [item["rejected_inspections"] for item in payload["items"]] == [2, 2]


def test_list_inspecoes_entrada_rejeitadas_ensaiador_returns_empty_when_no_rows() -> None:
    repository = MagicMock()
    repository.list_rejeitadas_ensaiador_by_branch.return_value = []

    use_case = ListInspecoesEntradaRejeitadasEnsaiadorUseCase(repository)
    result = use_case.execute(branch="02")

    payload = result.to_dict()
    assert payload["items"] == []
    assert payload["total_inspectors"] == 0
    assert payload["total_rejected"] == 0


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_entrada_rejeitadas_ensaiador_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesEntradaRejeitadasEnsaiadorUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.list_rejeitadas_ensaiador_by_branch.assert_not_called()
