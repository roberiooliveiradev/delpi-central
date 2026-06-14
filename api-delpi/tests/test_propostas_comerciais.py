from unittest.mock import MagicMock, patch

import pytest

from app.application.propostas_comerciais.use_cases.generate_proposta_comercial_pdf_use_case import (
    GeneratePropostaComercialPdfUseCase,
)
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
from app.domain.propostas_comerciais.services.proposta_comercial_pdf_export_overrides_service import (
    PropostaComercialPdfExportOverridesService,
)
from app.infrastructure.pdf.propostas_comerciais.proposta_comercial_pdf_renderer import (
    PropostaComercialPdfRenderer,
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
    assert PropostaComercialFormatter.format_icms_rate(12.0) == "12%"
    assert PropostaComercialFormatter.format_frete("F").startswith("FOB")
    assert PropostaComercialFormatter.format_embalagem("1") == "Embalagem padrão DELPI"


def _sample_detail() -> dict:
    return {
        "cabecalho": {
            "proposta_interna": "004845",
            "numero_ov": "OV003581",
            "oportunidade": "003581",
            "versao": "01",
            "revisao_oportunidade": "08",
            "data": "12/06/2026",
            "validade_dias": 30,
            "filial": "01",
            "status": "A",
            "soma_valores_r_mil": "R$ 1.507.588,55",
            "soma_valores_r_mil_numerico": 1507588.55,
        },
        "empresa": {
            "nome": "DELPI COMPONENTES LTDA",
            "cnpj": "01.379.126/0001-81",
            "inscricao_estadual": "253282144",
            "endereco": "RUA MANOEL FRANCISCO DA COSTA, 2020",
            "bairro": "CENTRO",
            "cidade": "JARAGUA DO SUL",
            "uf": "SC",
            "cep": "89257-207",
            "telefone": "(47) 3370-5502",
            "site": "www.delpi.com.br",
        },
        "cliente": {
            "codigo": "000204",
            "loja": "01",
            "nome": "AHT COOLING",
            "cnpj": "08.774.764/0003-08",
            "endereco": "RUA TESTE",
            "bairro": "CENTRO",
            "cidade": "NAVEGANTES",
            "uf": "SC",
            "cep": "88373-180",
            "telefone": "(47) 3347-9117",
        },
        "contato": {
            "codigo": "00489",
            "nome": "GUILHERME PERIN",
            "email": "guilherme@example.com",
            "telefone": None,
            "departamento": "COMPRAS",
        },
        "condicoes": {
            "codigo": "007",
            "descricao": "45 D.D.L.",
            "icms": "12%",
            "ipi": "5% CHICOTES ELETRICOS",
            "frete": "FOB — frete por conta do comprador",
            "embalagem": "Embalagem padrão DELPI",
        },
        "vendedor": {
            "codigo": "000013",
            "nome": "CÁSSIO ARNAUD",
            "email": "comercial2@delpi.com.br",
            "telefone": "(47) 3370-5502",
            "cargo": "VENDAS",
        },
        "observacoes": "Observacao teste\nLinha 2",
        "itens": [
            {
                "item": "01",
                "produto": "80016332",
                "descricao": "HARNESS FANS GKA MVP USA",
                "referencia_cliente": "989176",
                "ncm": "8544.42.00",
                "quantidade": 1.0,
                "unidade": "MI",
                "preco_unitario": "R$ 40.041,56",
                "preco_unitario_numerico": 40041.56,
                "valor_total": "R$ 40.041,56",
                "valor_total_numerico": 40041.56,
                "prazo_dias": 45,
                "lote_minimo": 0,
            }
        ],
    }


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
            "empresa_inscricao_estadual": "253282144",
            "empresa_endereco": "RUA MANOEL FRANCISCO DA COSTA, 2020",
            "empresa_bairro": "CENTRO",
            "empresa_cidade": "JARAGUA DO SUL",
            "empresa_uf": "SC",
            "empresa_cep": "89257207",
            "empresa_telefone": "(47) 3370-5500",
            "icms": 12.0,
            "ipi": "5% CHICOTES ELETRICOS",
            "frete": "F",
            "embalagem": "1",
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
    assert result["empresa"]["inscricao_estadual"] == "253282144"
    assert result["empresa"]["cep"] == "89257-207"
    assert result["condicoes"]["icms"] == "12%"
    assert result["condicoes"]["frete"].startswith("FOB")
    assert result["cliente"]["cnpj"] == "08.774.764/0003-08"
    assert result["itens"][0]["ncm"] == "8544.42.00"
    assert result["itens"][0]["prazo_dias"] == 45
    assert result["observacoes"] == "Observacao teste"


def test_proposta_comercial_pdf_renderer_returns_pdf_bytes() -> None:
    renderer = PropostaComercialPdfRenderer()
    pdf_bytes = renderer.render(_sample_detail())

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_generate_proposta_comercial_pdf_use_case_returns_filename() -> None:
    get_use_case = MagicMock(spec=GetPropostaComercialUseCase)
    get_use_case.execute.return_value = _sample_detail()
    renderer = MagicMock()
    renderer.render.return_value = b"%PDF-1.4 test"

    use_case = GeneratePropostaComercialPdfUseCase(
        get_proposta_comercial_use_case=get_use_case,
        pdf_renderer=renderer,
    )
    pdf_bytes, filename = use_case.execute("004845")

    get_use_case.execute.assert_called_once_with("004845")
    renderer.render.assert_called_once_with(_sample_detail())
    assert pdf_bytes.startswith(b"%PDF")
    assert filename == "proposta-OV003581.pdf"


def test_pdf_export_overrides_service_merges_editable_fields_only() -> None:
    detail = _sample_detail()
    merged = PropostaComercialPdfExportOverridesService.apply(
        detail,
        {
            "observacoes": " Texto ajustado \n",
            "vendedor": {"nome": "Vendedor Editado", "cargo": "COMERCIAL"},
            "condicoes": {"descricao": "30 D.D.L."},
            "contato": {"email": "novo@example.com"},
            "cabecalho": {"numero_ov": "OV999999"},
            "itens": [{"item": "99"}],
        },
    )

    assert merged["observacoes"] == "Texto ajustado"
    assert merged["vendedor"]["nome"] == "Vendedor Editado"
    assert merged["vendedor"]["cargo"] == "COMERCIAL"
    assert merged["vendedor"]["email"] == "comercial2@delpi.com.br"
    assert merged["condicoes"]["descricao"] == "30 D.D.L."
    assert merged["contato"]["email"] == "novo@example.com"
    assert merged["cabecalho"]["numero_ov"] == "OV003581"
    assert merged["itens"][0]["item"] == "01"


def test_generate_proposta_comercial_pdf_use_case_applies_overrides() -> None:
    get_use_case = MagicMock(spec=GetPropostaComercialUseCase)
    get_use_case.execute.return_value = _sample_detail()
    renderer = MagicMock()
    renderer.render.return_value = b"%PDF-1.4 test"

    use_case = GeneratePropostaComercialPdfUseCase(
        get_proposta_comercial_use_case=get_use_case,
        pdf_renderer=renderer,
    )
    overrides = {"observacoes": "Observacao editada"}
    pdf_bytes, filename = use_case.execute("004845", overrides=overrides)

    rendered_detail = renderer.render.call_args.args[0]
    assert rendered_detail["observacoes"] == "Observacao editada"
    assert pdf_bytes.startswith(b"%PDF")
    assert filename == "proposta-OV003581.pdf"


def test_export_proposta_comercial_pdf_route_returns_pdf() -> None:
    from app.interface.http.propostas_comerciais_controller import (
        export_proposta_comercial_pdf_route,
    )

    fake_pdf = b"%PDF-1.4 route-test"
    with patch(
        "app.interface.http.propostas_comerciais_controller.build_generate_proposta_comercial_pdf_use_case"
    ) as build_use_case:
        use_case = MagicMock()
        use_case.execute.return_value = (fake_pdf, "proposta-OV003581.pdf")
        build_use_case.return_value = use_case

        response = export_proposta_comercial_pdf_route("004845")

    assert response.status_code == 200
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF")
    assert response.headers["content-disposition"] == 'inline; filename="proposta-OV003581.pdf"'


def test_export_proposta_comercial_pdf_with_overrides_route_returns_pdf() -> None:
    from app.interface.http.propostas_comerciais_controller import (
        export_proposta_comercial_pdf_with_overrides_route,
    )
    from app.interface.http.schemas.proposta_comercial_pdf_schemas import (
        PropostaComercialPdfExportRequest,
    )

    fake_pdf = b"%PDF-1.4 route-test-overrides"
    with patch(
        "app.interface.http.propostas_comerciais_controller.build_generate_proposta_comercial_pdf_use_case"
    ) as build_use_case:
        use_case = MagicMock()
        use_case.execute.return_value = (fake_pdf, "proposta-OV003581.pdf")
        build_use_case.return_value = use_case

        response = export_proposta_comercial_pdf_with_overrides_route(
            "004845",
            PropostaComercialPdfExportRequest(observacoes="Observacao editada"),
        )

    use_case.execute.assert_called_once_with(
        "004845",
        overrides={"observacoes": "Observacao editada"},
    )
    assert response.status_code == 200
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF")


def test_export_proposta_comercial_pdf_route_not_found() -> None:
    from app.interface.http.propostas_comerciais_controller import (
        export_proposta_comercial_pdf_route,
    )

    with patch(
        "app.interface.http.propostas_comerciais_controller.build_generate_proposta_comercial_pdf_use_case"
    ) as build_use_case:
        use_case = MagicMock()
        use_case.execute.side_effect = PropostaComercialNotFoundError("004999")
        build_use_case.return_value = use_case

        response = export_proposta_comercial_pdf_route("004999")

    assert response.status_code == 404
