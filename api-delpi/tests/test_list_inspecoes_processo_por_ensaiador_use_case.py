from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_ensaiador_use_case import (
    ListInspecoesProcessoPorEnsaiadorUseCase,
)


def test_list_inspecoes_processo_por_ensaiador_normalizes_rows() -> None:
    repository = MagicMock()
    repository.list_por_ensaiador_by_branch.return_value = [
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Matricula_Ensaiador": "20364",
            "Nome_Ensaiador": "YAGO ROCHA",
            "Login_Ensaiador": "YAGO.ROCHA",
            "Qtde_OPs": 2222,
            "Qtde_Ensaios": 24079,
            "Qtde_Ensaios_Aprovados": 23274,
            "Qtde_Ensaios_Reprovados": 805,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_OPs_Aprovadas": 1523,
            "Qtde_OPs_Reprovadas": 699,
            "Qtde_Produtos": 724,
            "Qtde_Operacoes": 759,
            "Qtde_Ensaios_Distintos": 49,
            "Primeira_Data_Medicao_Date": date(2024, 11, 8),
            "Ultima_Data_Medicao_Date": date(2025, 10, 25),
            "Percentual_OPs_Aprovadas": 68.54,
            "Percentual_OPs_Reprovadas": 31.46,
            "Percentual_Ensaios_Aprovados": 96.66,
            "Percentual_Ensaios_Reprovados": 3.34,
        }
    ]

    use_case = ListInspecoesProcessoPorEnsaiadorUseCase(repository)
    result = use_case.execute(branch="02", limit=10)

    repository.list_por_ensaiador_by_branch.assert_called_once_with("02", limit=10)
    assert len(result) == 1
    assert result[0].to_dict() == {
        "filial": "02",
        "unidade": "Rio Bananal/ES",
        "matricula_ensaiador": "20364",
        "nome_ensaiador": "YAGO ROCHA",
        "login_ensaiador": "YAGO.ROCHA",
        "qtde_ops": 2222,
        "qtde_ensaios": 24079,
        "qtde_ensaios_aprovados": 23274,
        "qtde_ensaios_reprovados": 805,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 1523,
        "qtde_ops_reprovadas": 699,
        "qtde_produtos": 724,
        "qtde_operacoes": 759,
        "qtde_ensaios_distintos": 49,
        "primeira_data_medicao": "2024-11-08",
        "ultima_data_medicao": "2025-10-25",
        "percentual_ops_aprovadas": 68.54,
        "percentual_ops_reprovadas": 31.46,
        "percentual_ensaios_aprovados": 96.66,
        "percentual_ensaios_reprovados": 3.34,
    }


def test_list_inspecoes_processo_por_ensaiador_accepts_null_login() -> None:
    repository = MagicMock()
    repository.list_por_ensaiador_by_branch.return_value = [
        {
            "Filial": "01",
            "Unidade": "SC",
            "Matricula_Ensaiador": "99999",
            "Nome_Ensaiador": "SEM CADASTRO",
            "Login_Ensaiador": None,
            "Qtde_OPs": 1,
            "Qtde_Ensaios": 1,
            "Qtde_Ensaios_Aprovados": 1,
            "Qtde_Ensaios_Reprovados": 0,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_OPs_Aprovadas": 1,
            "Qtde_OPs_Reprovadas": 0,
            "Qtde_Produtos": 1,
            "Qtde_Operacoes": 1,
            "Qtde_Ensaios_Distintos": 1,
            "Primeira_Data_Medicao_Date": date(2025, 1, 1),
            "Ultima_Data_Medicao_Date": date(2025, 1, 1),
            "Percentual_OPs_Aprovadas": 100.0,
            "Percentual_OPs_Reprovadas": 0.0,
            "Percentual_Ensaios_Aprovados": 100.0,
            "Percentual_Ensaios_Reprovados": 0.0,
        }
    ]

    use_case = ListInspecoesProcessoPorEnsaiadorUseCase(repository)
    result = use_case.execute(branch="01", limit=10)

    assert result[0].login_ensaiador is None
    assert result[0].to_dict()["login_ensaiador"] is None


def test_list_inspecoes_processo_por_ensaiador_clamps_limit() -> None:
    repository = MagicMock()
    repository.list_por_ensaiador_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorEnsaiadorUseCase(repository)
    use_case.execute(branch="01", limit=999)

    repository.list_por_ensaiador_by_branch.assert_called_once_with("01", limit=50)


def test_list_inspecoes_processo_por_ensaiador_returns_empty_list() -> None:
    repository = MagicMock()
    repository.list_por_ensaiador_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorEnsaiadorUseCase(repository)
    result = use_case.execute(branch="01", limit=10)

    assert result == []


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_processo_por_ensaiador_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoPorEnsaiadorUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, limit=10)

    repository.list_por_ensaiador_by_branch.assert_not_called()
