from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_ranking_ensaio_use_case import (
    ListInspecoesProcessoRankingEnsaioUseCase,
)


def test_list_inspecoes_processo_ranking_ensaio_normalizes_rows() -> None:
    repository = MagicMock()
    repository.list_ranking_ensaio_by_branch.return_value = [
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Laboratorio": "LABFIS",
            "Codigo_Ensaio": "02",
            "Nome_Ensaio": "PRESSÃO DO TERMINAL",
            "Qtde_OPs": 1000,
            "Qtde_Ensaios": 1200,
            "Qtde_Ensaios_Aprovados": 1000,
            "Qtde_Ensaios_Reprovados": 200,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_OPs_Aprovadas": 800,
            "Qtde_OPs_Reprovadas": 200,
            "Qtde_Produtos": 50,
            "Qtde_Operacoes": 80,
            "Qtde_Ensaiadores": 10,
            "Primeira_Data_Medicao_Date": date(2024, 11, 8),
            "Ultima_Data_Medicao_Date": date(2026, 7, 13),
            "Percentual_OPs_Aprovadas": 80.00,
            "Percentual_OPs_Reprovadas": 20.00,
            "Percentual_Ensaios_Aprovados": 83.33,
            "Percentual_Ensaios_Reprovados": 16.67,
        }
    ]

    use_case = ListInspecoesProcessoRankingEnsaioUseCase(repository)
    result = use_case.execute(branch="02", limit=10)

    repository.list_ranking_ensaio_by_branch.assert_called_once_with("02", limit=10)
    assert len(result) == 1
    assert result[0].to_dict() == {
        "filial": "02",
        "unidade": "Rio Bananal/ES",
        "laboratorio": "LABFIS",
        "codigo_ensaio": "02",
        "nome_ensaio": "PRESSÃO DO TERMINAL",
        "qtde_ops": 1000,
        "qtde_ensaios": 1200,
        "qtde_ensaios_aprovados": 1000,
        "qtde_ensaios_reprovados": 200,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 800,
        "qtde_ops_reprovadas": 200,
        "qtde_produtos": 50,
        "qtde_operacoes": 80,
        "qtde_ensaiadores": 10,
        "primeira_data_medicao": "2024-11-08",
        "ultima_data_medicao": "2026-07-13",
        "percentual_ops_aprovadas": 80.0,
        "percentual_ops_reprovadas": 20.0,
        "percentual_ensaios_aprovados": 83.33,
        "percentual_ensaios_reprovados": 16.67,
    }


def test_list_inspecoes_processo_ranking_ensaio_clamps_limit() -> None:
    repository = MagicMock()
    repository.list_ranking_ensaio_by_branch.return_value = []

    use_case = ListInspecoesProcessoRankingEnsaioUseCase(repository)
    use_case.execute(branch="01", limit=999)

    repository.list_ranking_ensaio_by_branch.assert_called_once_with("01", limit=50)


def test_list_inspecoes_processo_ranking_ensaio_returns_empty_list() -> None:
    repository = MagicMock()
    repository.list_ranking_ensaio_by_branch.return_value = []

    use_case = ListInspecoesProcessoRankingEnsaioUseCase(repository)
    result = use_case.execute(branch="01", limit=10)

    assert result == []


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_processo_ranking_ensaio_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoRankingEnsaioUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, limit=10)

    repository.list_ranking_ensaio_by_branch.assert_not_called()
