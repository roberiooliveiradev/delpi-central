from unittest.mock import MagicMock

import pytest

from app.application.propostas_comerciais.use_cases.get_proposta_comercial_use_case import (
    GetPropostaComercialUseCase,
)
from app.application.propostas_comerciais.use_cases.list_propostas_comerciais_use_case import (
    ListPropostasComerciaisUseCase,
)
from app.domain.propostas_comerciais.exceptions import PropostaComercialNotFoundError
from app.domain.propostas_comerciais.services.proposta_comercial_formatter import (
    PropostaComercialFormatter,
)


def test_formatter_formats_document_fields() -> None:
    assert PropostaComercialFormatter.format_cnpj("08774764000308") == "08.774.764/0003-08"
    assert PropostaComercialFormatter.format_cep("88373180") == "88373-180"
    assert PropostaComercialFormatter.format_phone("(47) 3370-5502") == "(47) 3370-5502"
    assert PropostaComercialFormatter.format_phone("4733705502") == "(47) 3370-5502"
    assert PropostaComercialFormatter.format_ncm("85444200") == "8544.42.00"
    assert PropostaComercialFormatter.format_currency(40041.56) == "R$ 40.041,56"
    assert PropostaComercialFormatter.format_date("20260612") == "12/06/2026"
    assert PropostaComercialFormatter.format_integer_days(45.0) == 45
    assert PropostaComercialFormatter.format_minimum_lot(1000.0) == 1000


def test_list_propostas_comerciais_use_case_formats_items() -> None:
    repository = MagicMock()
    repository.list_active_recent.return_value = [
        {
            "proposta_interna": "004845",
            "oportunidade": "003581",
            "versao": "01",
            "data_proposta": "20260612",
            "cliente_nome": "AHT COOLING",
            "filial": "01",
            "quantidade_itens": 5,
        }
    ]

    use_case = ListPropostasComerciaisUseCase(repository)
    result = use_case.execute(limit=10)

    repository.list_active_recent.assert_called_once_with(limit=10)
    assert result["total"] == 1
    assert result["items"][0]["numero_ov"] == "OV003581"
    assert result["items"][0]["data"] == "12/06/2026"


def test_get_proposta_comercial_use_case_raises_when_missing() -> None:
    repository = MagicMock()
    repository.get_detail_rows.return_value = (None, [])

    use_case = GetPropostaComercialUseCase(repository)

    with pytest.raises(PropostaComercialNotFoundError):
        use_case.execute("999999")


def test_get_proposta_comercial_use_case_groups_detail() -> None:
    repository = MagicMock()
    repository.get_detail_rows.return_value = (
        {
            "proposta_interna": "004845",
            "oportunidade": "003581",
            "versao": "01",
            "revisao_oportunidade": "08",
            "data_proposta": "20260612",
            "validade_dias": 30,
            "status": "A",
            "filial": "01",
            "contato_codigo": "00489",
            "cliente_codigo": "000204",
            "cliente_loja": "01",
            "vendedor_codigo": "000013",
            "condicao_codigo": "007",
            "observacoes": "Observacao teste",
            "cliente_nome": "AHT COOLING",
            "cliente_cnpj": "08774764000308",
            "cliente_endereco": "RUA TESTE",
            "cliente_bairro": "CENTRO",
            "cliente_cidade": "NAVEGANTES",
            "cliente_uf": "SC",
            "cliente_cep": "88373180",
            "cliente_telefone": "33479117",
            "contato_nome": "GUILHERME PERIN",
            "contato_email": "guilherme@example.com",
            "contato_telefone": "",
            "contato_departamento": "COMPRAS",
            "condicao_descricao": "45 D.D.L.",
            "vendedor_nome": "CÁSSIO ARNAUD",
            "vendedor_email": "comercial2@delpi.com.br",
            "vendedor_telefone": "(47) 3370-5502",
            "vendedor_cargo": "VENDAS",
            "empresa_nome": "DELPI COMPONENTES LTDA",
            "empresa_cnpj": "01379126000181",
            "empresa_endereco": "RUA MANOEL FRANCISCO DA COSTA, 2020",
            "empresa_bairro": "CENTRO",
            "empresa_cidade": "JARAGUA DO SUL",
            "empresa_uf": "SC",
            "empresa_cep": "89256100",
            "empresa_telefone": "(47) 3370-5500",
            "soma_valores_r_mil": 1507588.55,
        },
        [
            {
                "item": "01",
                "produto": "80016332",
                "descricao": "HARNESS FANS GKA MVP USA",
                "referencia_cliente": "989176",
                "ncm": "85444200",
                "quantidade": 1.0,
                "unidade": "MI",
                "preco_unitario": 40041.56,
                "valor_total": 40041.56,
                "prazo_dias": 45.0,
                "lote_minimo": 0.0,
            }
        ],
    )

    use_case = GetPropostaComercialUseCase(repository)
    result = use_case.execute("004845")

    assert result["cabecalho"]["numero_ov"] == "OV003581"
    assert result["cabecalho"]["soma_valores_r_mil"] == "R$ 1.507.588,55"
    assert result["cabecalho"]["soma_valores_r_mil_numerico"] == 1507588.55
    assert result["empresa"]["site"] == "www.delpi.com.br"
    assert result["cliente"]["cnpj"] == "08.774.764/0003-08"
    assert result["itens"][0]["ncm"] == "8544.42.00"
    assert result["itens"][0]["prazo_dias"] == 45
    assert result["observacoes"] == "Observacao teste"
