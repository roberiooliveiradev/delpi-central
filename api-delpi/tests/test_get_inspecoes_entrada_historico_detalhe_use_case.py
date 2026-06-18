from unittest.mock import MagicMock

import pytest

from app.application.use_cases.inspecoes_entrada.get_inspecoes_entrada_historico_detalhe_use_case import (
    GetInspecoesEntradaHistoricoDetalheUseCase,
)


def _sample_header() -> dict:
    return {
        "Filial": "01",
        "Id_Inspecao": "01|000042999|2|0002|000532|01|10110388|AUTO000952",
        "Data_Recebimento": "20260611",
        "Hora_Recebimento": "09:39",
        "Data_Laudo": "2026-06-11",
        "Hora_Laudo": "10:06",
        "Nota_Fiscal": "000042999",
        "Serie_Nota_Fiscal": "2",
        "Item_Nota_Fiscal": "0002",
        "Codigo_Fornecedor": "000532",
        "Loja_Fornecedor": "01",
        "Nome_Fornecedor": "MULTIPRINT ETIQUETAS LTDA",
        "Codigo_Produto": "10110388",
        "Descricao_Produto": "ETIQUETA TECNICA BRANCA",
        "Lote": "AUTO000952",
        "Lote_Fornecedor": "",
        "Quantidade": 3000,
        "Unidade_Medida": "PC",
        "Codigo_Situacao": "3",
        "Status_Inspecao": "REJEITADA",
        "Resultado_Resumo": "REJEITADA",
        "Codigo_Laudo": "E",
        "Quantidade_Aprovada": None,
        "Quantidade_Rejeitada": 3000,
        "Justificativa_Laudo": "",
        "Matricula_Ensaiador": "30006",
        "Nome_Ensaiador": "NATHALIA FERNANDES SALES",
        "Login_Ensaiador": "NATHALIA",
        "Qtde_Ensaios": 6,
        "Qtde_Ensaios_Reprovados": 1,
        "Eh_Aprovada": 0,
        "Eh_Rejeitada": 1,
    }


def _base_test_row(**overrides: object) -> dict:
    row = {
        "Codigo_Ensaio": "011",
        "Nome_Ensaio": "CERTIFICADO/LAUDO TÉCNICO",
        "Especificacao_Textual": "CONFORME",
        "Valor_Nominal": None,
        "Limite_Inferior_Espec": None,
        "Limite_Superior_Espec": None,
        "Limite_Inferior_Controle": None,
        "Limite_Superior_Controle": None,
        "Regra_Min_Max": None,
        "Unidade_Especificacao": None,
        "Medicao_Textual": None,
        "Medicao_Numerica": None,
        "Indicador_Medicao_Numerica": None,
        "Fonte_Medicao": None,
        "Valor_Medido": None,
        "Especificacao_Esperada": "CONFORME",
        "Codigo_Resultado": "A",
        "Data_Medicao": "2026-06-11",
        "Hora_Medicao": "10:06",
        "Numero_Amostra": 1,
        "Chave_Qer": "00006865",
        "Numero_Sequencia": "UCUYZT",
        "Laboratorio": "LABFIS",
        "Matricula_Ensaiador": "30006",
        "Nome_Ensaiador": "NATHALIA FERNANDES SALES",
        "Login_Ensaiador": "NATHALIA",
    }
    row.update(overrides)
    return row


def _sample_tests() -> list[dict]:
    specs = [
        ("011", "CERTIFICADO/LAUDO TÉCNICO", "CONFORME", "A"),
        ("022", "IDENTIFICAÇÃO E EMBALAGEM", "EMBALADO EM ROLOS OU CARTELAS PLÁSTICAS", "A"),
        ("030", "DETALHES DO ITEM", "CONFECCIONADA EM ACETATO DE RAYON", "R"),
        ("031", "ACABAMENTO", "SUPERFÍCIE ACETINADA E LISA, COM ÓTIMA ANCORAGEM DE TINTA", "A"),
        ("032", "COR PADRÃO", "BRANCO", "A"),
        ("033", "MATERIAL", "ACETATO DE RAYON, TECIDO TÉCNICO COMPOSTO POR FIBRAS", "A"),
    ]
    rows = []
    for code, name, spec, result in specs:
        measured_text = None
        measured_value = None
        measurement_source = None
        if code == "030":
            measured_text = "Correto Etiqueta F- . Venho -F errada."
            measured_value = measured_text
            measurement_source = "QEQ"
        rows.append(
            _base_test_row(
                Codigo_Ensaio=code,
                Nome_Ensaio=name,
                Especificacao_Textual=spec,
                Especificacao_Esperada=spec,
                Codigo_Resultado=result,
                Hora_Medicao="10:03" if code == "030" else "10:06",
                Medicao_Textual=measured_text,
                Valor_Medido=measured_value,
                Fonte_Medicao=measurement_source,
            )
        )
    return rows


def test_get_inspecoes_entrada_historico_detalhe_returns_enriched_tests() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = _sample_tests()

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )

    assert result is not None
    payload = result.to_dict()
    assert payload["summary"]["product_description"] == "ETIQUETA TECNICA BRANCA"
    assert len(payload["tests"]) == 6
    rejected = payload["tests"][2]
    assert rejected["test_code"] == "030"
    assert rejected["test_name"] == "DETALHES DO ITEM"
    assert rejected["expected_specification"] == "CONFECCIONADA EM ACETATO DE RAYON"
    assert rejected["text_specification"] == "CONFECCIONADA EM ACETATO DE RAYON"
    assert rejected["text_measured_value"] == "Correto Etiqueta F- . Venho -F errada."
    assert rejected["measured_value"] == "Correto Etiqueta F- . Venho -F errada."
    assert rejected["measurement_source"] == "QEQ"
    assert rejected["numeric_measured_value"] is None
    assert rejected["result"] == "REPROVADO"
    assert payload["tests"][0]["test_name"] == "CERTIFICADO/LAUDO TÉCNICO"
    assert payload["tests"][0]["laboratory"] == "LABFIS"
    assert payload["tests"][0]["sample_number"] == 1
    assert payload["totals"] == {
        "tests_count": 6,
        "approved_tests_count": 5,
        "failed_tests_count": 1,
    }


def test_get_inspecoes_entrada_historico_detalhe_maps_textual_measurement() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="003",
            Nome_Ensaio="MATERIAL DA ISOLAÇÃO",
            Especificacao_Textual="PVC",
            Especificacao_Esperada="PVC",
            Medicao_Textual="PVC",
            Valor_Medido="PVC",
            Fonte_Medicao="QEQ",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["text_specification"] == "PVC"
    assert test["text_measured_value"] == "PVC"
    assert test["measurement_source"] == "QEQ"
    assert test["measured_value"] == "PVC"
    assert test["numeric_measured_value"] is None
    assert test["nominal_value"] is None


def test_get_inspecoes_entrada_historico_detalhe_maps_numeric_measurement() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="0001",
            Nome_Ensaio="DIAMETRO EXTERNO",
            Especificacao_Textual=None,
            Especificacao_Esperada="Nominal: 6,40 | Min: 6,20 | Max: 6,60 UN",
            Valor_Nominal="6,40",
            Limite_Inferior_Espec="6,20",
            Limite_Superior_Espec="6,60",
            Regra_Min_Max="1",
            Unidade_Especificacao="UN",
            Medicao_Numerica="6.40",
            Indicador_Medicao_Numerica="A",
            Valor_Medido="6.40",
            Fonte_Medicao="QES",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000132683|1|0001|001499|01|10020119|AUTO000993",
    )

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["nominal_value"] == "6,40"
    assert test["lower_spec_limit"] == "6,20"
    assert test["upper_spec_limit"] == "6,60"
    assert test["numeric_measured_value"] == "6.40"
    assert test["measurement_source"] == "QES"
    assert test["measured_value"] == "6.40"
    assert test["text_measured_value"] is None


def test_get_inspecoes_entrada_historico_detalhe_prefers_qes_for_measured_value() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="0001",
            Medicao_Textual="texto",
            Medicao_Numerica="6.40",
            Valor_Medido="6.40",
            Fonte_Medicao="QES",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000132683|1|0001|001499|01|10020119|AUTO000993",
    )

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["measured_value"] == "6.40"
    assert test["measurement_source"] == "QES"


def test_get_inspecoes_entrada_historico_detalhe_uses_qeq_when_no_numeric_measurement() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="003",
            Medicao_Textual="PVC",
            Valor_Medido="PVC",
            Fonte_Medicao="QEQ",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000132683|1|0001|001499|01|10020119|AUTO000993",
    )

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["measured_value"] == "PVC"
    assert test["measurement_source"] == "QEQ"


def test_get_inspecoes_entrada_historico_detalhe_does_not_invent_measurements() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="099",
            Medicao_Textual=None,
            Medicao_Numerica=None,
            Valor_Medido=None,
            Fonte_Medicao=None,
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["measured_value"] is None
    assert test["text_measured_value"] is None
    assert test["numeric_measured_value"] is None
    assert test["measurement_source"] is None


def test_get_inspecoes_entrada_historico_detalhe_returns_none_when_not_found() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = None

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(branch="01", inspection_id="missing")

    assert result is None
    repository.list_tests_by_inspection_header.assert_not_called()


def test_get_inspecoes_entrada_historico_detalhe_preserves_leading_zeros() -> None:
    repository = MagicMock()
    header = _sample_header()
    header["Item_Nota_Fiscal"] = "0002"
    repository.get_historico_header_by_inspection_id.return_value = header
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="030",
            Nome_Ensaio="DETALHES DO ITEM",
            Especificacao_Textual="CONFECCIONADA EM ACETATO DE RAYON",
            Especificacao_Esperada="CONFECCIONADA EM ACETATO DE RAYON",
            Codigo_Resultado="R",
            Hora_Medicao="10:03",
            Medicao_Textual="Correto Etiqueta F- . Venho -F errada.",
            Valor_Medido="Correto Etiqueta F- . Venho -F errada.",
            Fonte_Medicao="QEQ",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(
        branch="01",
        inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952",
    )

    assert result is not None
    payload = result.to_dict()
    assert payload["summary"]["invoice_item"] == "0002"
    assert payload["tests"][0]["test_code"] == "030"


@pytest.mark.parametrize("branch", ["03", ""])
def test_get_inspecoes_entrada_historico_detalhe_rejects_invalid_branch(branch: str) -> None:
    repository = MagicMock()
    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)

    with pytest.raises(ValueError, match="branch inválida"):
        use_case.execute(branch=branch, inspection_id="01|x")


def test_get_inspecoes_entrada_historico_detalhe_requires_inspection_id() -> None:
    repository = MagicMock()
    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)

    with pytest.raises(ValueError, match="inspection_id"):
        use_case.execute(branch="01", inspection_id="  ")


def test_get_inspecoes_entrada_historico_detalhe_maps_unknown_result_code() -> None:
    repository = MagicMock()
    repository.get_historico_header_by_inspection_id.return_value = _sample_header()
    repository.list_tests_by_inspection_header.return_value = [
        _base_test_row(
            Codigo_Ensaio="099",
            Nome_Ensaio="ENSAIO TESTE",
            Especificacao_Esperada="ESPEC",
            Codigo_Resultado="X",
            Numero_Amostra=None,
            Chave_Qer="",
            Numero_Sequencia="",
            Laboratorio="",
        )
    ]

    use_case = GetInspecoesEntradaHistoricoDetalheUseCase(repository)
    result = use_case.execute(branch="01", inspection_id="01|000042999|2|0002|000532|01|10110388|AUTO000952")

    assert result is not None
    test = result.to_dict()["tests"][0]
    assert test["result"] == "NAO_IDENTIFICADO"
    assert test["result_code"] == "X"
    assert test["measured_value"] is None
