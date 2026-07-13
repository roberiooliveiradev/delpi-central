from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_processo.get_inspecoes_processo_historico_detalhe_use_case import (
    GetInspecoesProcessoHistoricoDetalheUseCase,
)


def test_get_inspecoes_processo_historico_detalhe_normalizes() -> None:
    repository = MagicMock()
    repository.get_historico_cabecalho_by_op.return_value = {
        "Filial": "02",
        "Unidade": "Rio Bananal/ES",
        "Ordem_Producao": "10565201002",
        "Codigo_Produto": "50233817",
        "Descricao_Produto": "CB18BRAN",
        "Revisao_Produto": "00",
        "Quantidade_OP": 4.05,
        "Chave_Cabecalho_Inspecao": "00059332",
        "Origem_Inspecao": "MATA650",
        "Qtde_Ensaios": 12,
        "Qtde_Ensaios_Aprovados": 12,
        "Qtde_Ensaios_Reprovados": 0,
        "Qtde_Ensaios_Tolerancia": 0,
        "Qtde_Operacoes": 1,
        "Qtde_Ensaiadores": 1,
        "Resultado_Inspecao_Codigo": "A",
        "Resultado_Inspecao": "APROVADO",
        "Primeira_Data_Medicao_Date": date(2026, 7, 12),
        "Ultima_Data_Medicao_Date": date(2026, 7, 12),
        "Ultima_Hora_Medicao": "09:16",
        "Matricula_Ultimo_Ensaiador": "20266",
        "Nome_Ultimo_Ensaiador": "MAIANA SANTOS DE JESUS",
    }
    repository.list_historico_detalhe_itens_by_op.return_value = [
        {
            "Inspecao_Id": "I1",
            "Ensaio_Id": "E1",
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Ordem_Producao": "10565201002",
            "Codigo_Produto": "50233817",
            "Descricao_Produto": "CB18BRAN",
            "Revisao_Produto": "00",
            "Roteiro": "01",
            "Operacao": "01",
            "Recurso": "CT-01B",
            "Ferramenta": "23-022",
            "Centro_Trabalho": "CT-01B",
            "Descricao_Operacao": "CORTAR E APLICAR 100",
            "Laboratorio": "LABFIS",
            "Codigo_Ensaio": "20",
            "Nome_Ensaio": "PRESSÃO",
            "Especificacao_Textual": None,
            "Valor_Nominal": "1.20",
            "Limite_Inferior_Especificacao": "1.00",
            "Limite_Superior_Especificacao": "1.50",
            "Limite_Inferior_Controle": None,
            "Limite_Superior_Controle": None,
            "Regra_Min_Max": None,
            "Unidade_Especificacao": "mm",
            "Especificacao_Esperada": "1.00-1.50",
            "Medicao_Textual": None,
            "Medicao_Numerica_A": 1.23,
            "Medicao_Numerica_N": 1.23,
            "Medicao_Numerica": "1.23",
            "Modo_Medicao_Numerica": "SINGLE",
            "Fonte_Medicao": "QPS",
            "Resultado_Codigo": "A",
            "Resultado": "APROVADO",
            "Data_Medicao_Date": date(2026, 7, 12),
            "Hora_Medicao": "09:16",
            "Matricula_Ensaiador": "20266",
            "Nome_Ensaiador": "MAIANA SANTOS DE JESUS",
            "Chave_Medicao": "K1",
            "QPR_RECNO": 10,
        },
        {
            "Inspecao_Id": "I2",
            "Ensaio_Id": "E2",
            "Filial": "02",
            "Unidade": "Rio Bananal/ES",
            "Ordem_Producao": "10565201002",
            "Codigo_Produto": "50233817",
            "Descricao_Produto": "CB18BRAN",
            "Revisao_Produto": "00",
            "Roteiro": "01",
            "Operacao": "01",
            "Recurso": "CT-01B",
            "Ferramenta": "23-022",
            "Centro_Trabalho": "CT-01B",
            "Descricao_Operacao": "CORTAR E APLICAR 100",
            "Laboratorio": "LABFIS",
            "Codigo_Ensaio": "21",
            "Nome_Ensaio": "OUTRO",
            "Especificacao_Textual": None,
            "Valor_Nominal": None,
            "Limite_Inferior_Especificacao": None,
            "Limite_Superior_Especificacao": None,
            "Limite_Inferior_Controle": None,
            "Limite_Superior_Controle": None,
            "Regra_Min_Max": None,
            "Unidade_Especificacao": None,
            "Especificacao_Esperada": None,
            "Medicao_Textual": "OK",
            "Medicao_Numerica_A": None,
            "Medicao_Numerica_N": None,
            "Medicao_Numerica": None,
            "Modo_Medicao_Numerica": None,
            "Fonte_Medicao": "QPS",
            "Resultado_Codigo": "A",
            "Resultado": "APROVADO",
            "Data_Medicao_Date": date(2026, 7, 12),
            "Hora_Medicao": "09:17",
            "Matricula_Ensaiador": "20266",
            "Nome_Ensaiador": "MAIANA SANTOS DE JESUS",
            "Chave_Medicao": "K2",
            "QPR_RECNO": 11,
        },
    ]

    use_case = GetInspecoesProcessoHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="02",
        ordem_producao="10565201002",
        page=1,
        page_size=1,
    )

    assert result is not None
    repository.get_historico_cabecalho_by_op.assert_called_once_with(
        "02",
        ordem_producao="10565201002",
    )
    repository.list_historico_detalhe_itens_by_op.assert_called_once_with(
        "02",
        ordem_producao="10565201002",
        offset=0,
        fetch_next=2,
    )
    payload = result.to_dict()
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["has_next"] is True
    assert payload["cabecalho"]["ordem_producao"] == "10565201002"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["codigo_ensaio"] == "20"
    assert payload["items"][0]["medicao_numerica_a"] == 1.23
    assert payload["items"][0]["medicao_textual"] is None


def test_get_inspecoes_processo_historico_detalhe_returns_none_when_missing() -> None:
    repository = MagicMock()
    repository.get_historico_cabecalho_by_op.return_value = None

    use_case = GetInspecoesProcessoHistoricoDetalheUseCase(repository)
    result = use_case.execute(branch="01", ordem_producao="999")

    assert result is None
    repository.list_historico_detalhe_itens_by_op.assert_not_called()


def test_get_inspecoes_processo_historico_detalhe_clamps_page_size() -> None:
    repository = MagicMock()
    repository.get_historico_cabecalho_by_op.return_value = {
        "Filial": "01",
        "Unidade": "SC",
        "Ordem_Producao": "1",
        "Codigo_Produto": "X",
        "Descricao_Produto": "",
        "Revisao_Produto": "",
        "Quantidade_OP": 1,
        "Chave_Cabecalho_Inspecao": "",
        "Origem_Inspecao": "",
        "Qtde_Ensaios": 0,
        "Qtde_Ensaios_Aprovados": 0,
        "Qtde_Ensaios_Reprovados": 0,
        "Qtde_Ensaios_Tolerancia": 0,
        "Qtde_Operacoes": 0,
        "Qtde_Ensaiadores": 0,
        "Resultado_Inspecao_Codigo": "A",
        "Resultado_Inspecao": "APROVADO",
        "Primeira_Data_Medicao_Date": None,
        "Ultima_Data_Medicao_Date": None,
        "Ultima_Hora_Medicao": None,
        "Matricula_Ultimo_Ensaiador": "",
        "Nome_Ultimo_Ensaiador": "",
    }
    repository.list_historico_detalhe_itens_by_op.return_value = []

    use_case = GetInspecoesProcessoHistoricoDetalheUseCase(repository)
    use_case.execute(branch="01", ordem_producao="1", page=2, page_size=999)

    repository.list_historico_detalhe_itens_by_op.assert_called_once_with(
        "01",
        ordem_producao="1",
        offset=200,
        fetch_next=201,
    )


@pytest.mark.parametrize("branch", ["03", "", "1"])
def test_get_inspecoes_processo_historico_detalhe_rejects_invalid_branch(
    branch: str,
) -> None:
    repository = MagicMock()
    use_case = GetInspecoesProcessoHistoricoDetalheUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, ordem_producao="1")

    repository.get_historico_cabecalho_by_op.assert_not_called()


def test_get_inspecoes_processo_historico_detalhe_rejects_blank_op() -> None:
    repository = MagicMock()
    use_case = GetInspecoesProcessoHistoricoDetalheUseCase(repository)

    with pytest.raises(ValueError, match="ordem_producao"):
        use_case.execute(branch="01", ordem_producao="  ")

    repository.get_historico_cabecalho_by_op.assert_not_called()
