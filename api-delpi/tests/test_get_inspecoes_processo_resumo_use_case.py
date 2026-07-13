from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.get_inspecoes_processo_resumo_use_case import (
    GetInspecoesProcessoResumoUseCase,
)


def test_get_inspecoes_processo_resumo_normalizes_row() -> None:
    repository = MagicMock()
    repository.get_resumo_by_branch.return_value = {
        "Filial": "02",
        "Unidade": "Rio Bananal/ES",
        "Qtde_OPs": 33641,
        "Qtde_Ensaios": 490623,
        "Qtde_Ensaios_Aprovados": 485203,
        "Qtde_Ensaios_Reprovados": 5420,
        "Qtde_Ensaios_Tolerancia": 0,
        "Qtde_OPs_Aprovadas": 29425,
        "Qtde_OPs_Reprovadas": 4216,
        "Qtde_OPs_Tolerancia": 0,
        "Qtde_OPs_Nao_Identificadas": 0,
        "Qtde_Produtos": 2001,
        "Qtde_Operacoes": 4732,
        "Qtde_Ensaiadores": 85,
        "Primeira_Data_Medicao_Date": date(2023, 8, 23),
        "Ultima_Data_Medicao_Date": date(2026, 7, 12),
        "Percentual_OPs_Aprovadas": 87.47,
        "Percentual_OPs_Reprovadas": 12.53,
        "Percentual_Ensaios_Aprovados": 98.90,
        "Percentual_Ensaios_Reprovados": 1.10,
    }

    use_case = GetInspecoesProcessoResumoUseCase(repository)
    result = use_case.execute(branch="02")

    repository.get_resumo_by_branch.assert_called_once_with("02")
    assert result.to_dict() == {
        "filial": "02",
        "unidade": "Rio Bananal/ES",
        "qtde_ops": 33641,
        "qtde_ensaios": 490623,
        "qtde_ensaios_aprovados": 485203,
        "qtde_ensaios_reprovados": 5420,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 29425,
        "qtde_ops_reprovadas": 4216,
        "qtde_ops_tolerancia": 0,
        "qtde_ops_nao_identificadas": 0,
        "qtde_produtos": 2001,
        "qtde_operacoes": 4732,
        "qtde_ensaiadores": 85,
        "primeira_data_medicao": "2023-08-23",
        "ultima_data_medicao": "2026-07-12",
        "percentual_ops_aprovadas": 87.47,
        "percentual_ops_reprovadas": 12.53,
        "percentual_ensaios_aprovados": 98.90,
        "percentual_ensaios_reprovados": 1.10,
    }


def test_get_inspecoes_processo_resumo_returns_zeros_when_row_missing() -> None:
    repository = MagicMock()
    repository.get_resumo_by_branch.return_value = None

    use_case = GetInspecoesProcessoResumoUseCase(repository)
    result = use_case.execute(branch="01")

    assert result.to_dict() == {
        "filial": "01",
        "unidade": "",
        "qtde_ops": 0,
        "qtde_ensaios": 0,
        "qtde_ensaios_aprovados": 0,
        "qtde_ensaios_reprovados": 0,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 0,
        "qtde_ops_reprovadas": 0,
        "qtde_ops_tolerancia": 0,
        "qtde_ops_nao_identificadas": 0,
        "qtde_produtos": 0,
        "qtde_operacoes": 0,
        "qtde_ensaiadores": 0,
        "primeira_data_medicao": None,
        "ultima_data_medicao": None,
        "percentual_ops_aprovadas": 0.0,
        "percentual_ops_reprovadas": 0.0,
        "percentual_ensaios_aprovados": 0.0,
        "percentual_ensaios_reprovados": 0.0,
    }


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_get_inspecoes_processo_resumo_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = GetInspecoesProcessoResumoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch)

    repository.get_resumo_by_branch.assert_not_called()
