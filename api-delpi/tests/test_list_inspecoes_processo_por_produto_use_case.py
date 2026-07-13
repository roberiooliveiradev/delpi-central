from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_produto_use_case import (
    ListInspecoesProcessoPorProdutoUseCase,
)


def test_list_inspecoes_processo_por_produto_normalizes_rows() -> None:
    repository = MagicMock()
    repository.list_por_produto_by_branch.return_value = [
        {
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Codigo_Produto": "50232464",
            "Descricao_Produto": "CF20VERM-00212/06/03-6314-0000",
            "Revisao_Produto": "05",
            "Qtde_OPs": 79,
            "Qtde_Ensaios": 1416,
            "Qtde_Ensaios_Aprovados": 1194,
            "Qtde_Ensaios_Reprovados": 222,
            "Qtde_Ensaios_Tolerancia": 0,
            "Qtde_OPs_Aprovadas": 8,
            "Qtde_OPs_Reprovadas": 71,
            "Qtde_OPs_Tolerancia": 0,
            "Qtde_Ensaios_Distintos": 14,
            "Qtde_Operacoes": 3,
            "Qtde_Ensaiadores": 18,
            "Primeira_Data_Medicao_Date": date(2025, 2, 19),
            "Ultima_Data_Medicao_Date": date(2025, 6, 24),
            "Percentual_OPs_Aprovadas": 10.13,
            "Percentual_OPs_Reprovadas": 89.87,
            "Percentual_Ensaios_Aprovados": 84.32,
            "Percentual_Ensaios_Reprovados": 15.68,
        }
    ]

    use_case = ListInspecoesProcessoPorProdutoUseCase(repository)
    result = use_case.execute(branch="02", limit=10)

    repository.list_por_produto_by_branch.assert_called_once_with("02", limit=10)
    assert len(result) == 1
    assert result[0].to_dict() == {
        "filial": "02",
        "unidade": "Rio Bananal/ES",
        "codigo_produto": "50232464",
        "descricao_produto": "CF20VERM-00212/06/03-6314-0000",
        "revisao_produto": "05",
        "qtde_ops": 79,
        "qtde_ensaios": 1416,
        "qtde_ensaios_aprovados": 1194,
        "qtde_ensaios_reprovados": 222,
        "qtde_ensaios_tolerancia": 0,
        "qtde_ops_aprovadas": 8,
        "qtde_ops_reprovadas": 71,
        "qtde_ops_tolerancia": 0,
        "qtde_ensaios_distintos": 14,
        "qtde_operacoes": 3,
        "qtde_ensaiadores": 18,
        "primeira_data_medicao": "2025-02-19",
        "ultima_data_medicao": "2025-06-24",
        "percentual_ops_aprovadas": 10.13,
        "percentual_ops_reprovadas": 89.87,
        "percentual_ensaios_aprovados": 84.32,
        "percentual_ensaios_reprovados": 15.68,
    }


def test_list_inspecoes_processo_por_produto_clamps_limit() -> None:
    repository = MagicMock()
    repository.list_por_produto_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorProdutoUseCase(repository)
    use_case.execute(branch="01", limit=999)

    repository.list_por_produto_by_branch.assert_called_once_with("01", limit=50)


def test_list_inspecoes_processo_por_produto_returns_empty_list() -> None:
    repository = MagicMock()
    repository.list_por_produto_by_branch.return_value = []

    use_case = ListInspecoesProcessoPorProdutoUseCase(repository)
    result = use_case.execute(branch="01", limit=10)

    assert result == []


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_list_inspecoes_processo_por_produto_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = ListInspecoesProcessoPorProdutoUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, limit=10)

    repository.list_por_produto_by_branch.assert_not_called()
