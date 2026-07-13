"""Use case — auditoria de apontamentos sem inspeção de processo."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_auditoria_apontamentos_use_case import (
    ListInspecoesProcessoAuditoriaApontamentosUseCase,
)


def test_list_auditoria_apontamentos_normalizes_rows() -> None:
    repository = MagicMock()
    repository.list_auditoria_apontamentos_page.return_value = (
        {
            "Operadores_Pendentes": 1,
            "Apontamentos_Pendentes": 1,
            "Ops_Operacoes_Pendentes": 1,
            "Apontamentos_Com_Inspecao": 3,
            "Apontamentos_Total": 4,
        },
        [
            {
                "Filial": "02",
                "Cod_Operador": "000177",
                "Login_Operador": "CARLA.JESUS",
                "Nome_Operador": "CARLA SOARES DE JESUS",
                "Ordem_Producao": "10543901002",
                "Codigo_Produto": "50233817",
                "Descricao_Produto": "PRODUTO X",
                "Revisao_Produto": "",
                "Operacao": "01",
                "Centro_Trabalho": "CT-01A",
                "Data_Producao": date(2026, 7, 13),
                "Hora_Inicio": "080000",
                "Hora_Final": "100000",
                "Qtde_Apontamentos": 2,
                "Operador_Inspecionou": 0,
                "Tem_Inspecao_Na_Op_Operacao": 1,
                "Tem_Inspecao_Amarrada": 0,
                "Tem_Inspecao_Executada": 0,
            }
        ],
    )

    use_case = ListInspecoesProcessoAuditoriaApontamentosUseCase(repository)
    result = use_case.execute(branch="02", data="2026-07-13", page=1, page_size=50)

    assert result.data == "2026-07-13"
    assert result.summary.apontamentos_total == 4
    assert result.summary.apontamentos_pendentes == 1
    item = result.items[0]
    assert item.login_operador == "CARLA.JESUS"
    assert item.operador_inspecionou is False
    assert item.tem_inspecao_na_op_operacao is True
    assert item.tem_inspecao_executada is False


def test_list_auditoria_apontamentos_defaults_data_to_today() -> None:
    repository = MagicMock()
    repository.list_auditoria_apontamentos_page.return_value = ({}, [])

    use_case = ListInspecoesProcessoAuditoriaApontamentosUseCase(repository)
    result = use_case.execute(branch="01")

    assert result.data == date.today().isoformat()
    assert result.items == []
    assert result.summary.apontamentos_total == 0


def test_list_auditoria_apontamentos_rejects_invalid_branch() -> None:
    use_case = ListInspecoesProcessoAuditoriaApontamentosUseCase(MagicMock())
    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch="03")


def test_list_auditoria_apontamentos_rejects_invalid_data() -> None:
    use_case = ListInspecoesProcessoAuditoriaApontamentosUseCase(MagicMock())
    with pytest.raises(ValueError, match="data inválida"):
        use_case.execute(branch="01", data="13/07/2026")


def test_list_auditoria_apontamentos_detects_has_next() -> None:
    repository = MagicMock()
    repository.list_auditoria_apontamentos_page.return_value = (
        {
            "Operadores_Pendentes": 1,
            "Apontamentos_Pendentes": 3,
            "Ops_Operacoes_Pendentes": 3,
            "Apontamentos_Com_Inspecao": 0,
            "Apontamentos_Total": 3,
        },
        [
            {"Filial": "01", "Ordem_Producao": f"OP{i}", "Operacao": "01"}
            for i in range(3)
        ],
    )

    use_case = ListInspecoesProcessoAuditoriaApontamentosUseCase(repository)
    result = use_case.execute(branch="01", data="2026-07-13", page=1, page_size=2)

    assert result.has_next is True
    assert len(result.items) == 2
