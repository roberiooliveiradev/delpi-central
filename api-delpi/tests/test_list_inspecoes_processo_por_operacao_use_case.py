from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_operacao_use_case import (
    ListInspecoesProcessoPorOperacaoUseCase,
)


def test_list_inspecoes_processo_por_operacao_normalizes_rows() -> None:
    repository = MagicMock()
    repository.list_por_operacao_by_branch.return_value = [
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Codigo_Produto": "50232465",
            "Descricao_Produto": "CF20AZUL-00232/06/11-6314-0000",
            "Revisao_Produto": "02",
            "Roteiro": "01",
            "Operacao": "01",
            "Recurso": "CT-01A",
            "Ferramenta": "23-022",
            "Centro_Trabalho": "CT-01A",
            "Descricao_Operacao": "CORTAR E APLICAR 100",
            "Qtde_OPs": 474,
            "Qtde_Ensaios": 4908,
            "Qtde_Ensaios_Aprovados": 4714,
            "Qtde_Ensaios_Reprovados": 194,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_OPs_Aprovadas": 317,
            "Qtde_OPs_Reprovadas": 157,
            "Qtde_OPs_Tolerancia": 0,
            "Qtde_Ensaios_Distintos": 8,
            "Qtde_Ensaiadores": 26,
            "Primeira_Data_Medicao_Date": date(2024, 11, 8),
            "Ultima_Data_Medicao_Date": date(2026, 7, 11),
            "Percentual_OPs_Aprovadas": 66.88,
            "Percentual_OPs_Reprovadas": 33.12,
            "Percentual_Ensaios_Aprovados": 96.05,
            "Percentual_Ensaios_Reprovados": 3.95,
        }
    ]

    use_case = ListInspecoesProcessoPorOperacaoUseCase(repository)
    result = use_case.execute(branch="02", limit=10)

    repository.list_por_operacao_by_branch.assert_called_once_with("02", limit=10)
    assert len(result) == 1
    assert result[0].to_dict() == {
        "filial": "02",
        "unidade": "Rio Bananal/ES",
        "codigo_produto": "50232465",
        "descricao_produto": "CF20AZUL-00232/06/11-6314-0000",
        "revisao_produto": "02",
        "roteiro": "01",
        "operacao": "01",
        "recurso": "CT-01A",
        "ferramenta": "23-022",
        "centro_trabalho": "CT-01A",
        "descricao_operacao": "CORTAR E APLICAR 100",
        "qtde_ops": 474,
        "qtde_ensaios": 4908,
        "qtde_ensaios_aprovados": 4714,
        "qtde_ensaios_reprovados": 194,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 317,
        "qtde_ops_reprovadas": 157,
        "qtde_ops_tolerancia": 0,
        "qtde_ensaios_distintos": 8,
        "qtde_ensaiadores": 26,
        "primeira_data_medicao": "2024-11-08",
        "ultima_data_medicao": "2026-07-11",
        "percentual_ops_aprovadas": 66.88,
        "percentual_ops_reprovadas": 33.12,
        "percentual_ensaios_aprovados": 96.05,
        "percentual_ensaios_reprovados": 3.95,
    }


def test_list_inspecoes_processo_por_operacao_clamps_limit() -> None:
    repository = MagicMock()
    repository.list_por_operacao_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorOperacaoUseCase(repository)
    use_case.execute(branch="01", limit=999)

    repository.list_por_operacao_by_branch.assert_called_once_with("01", limit=50)


def test_list_inspecoes_processo_por_operacao_returns_empty_list() -> None:
    repository = MagicMock()
    repository.list_por_operacao_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorOperacaoUseCase(repository)
    result = use_case.execute(branch="01", limit=10)

    assert result == []


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_processo_por_operacao_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoPorOperacaoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, limit=10)

    repository.list_por_operacao_by_branch.assert_not_called()
