from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _sample_analyser_payload():
    return {
        "product": {
            "group_code": "9026",
            "code": "90260148",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "active": "S",
            "blocked": "2",
            "customer_reference": "3E 4270 G02",
            "unit": "MI",
            "default_warehouse": "01",
            "last_purchase_price": 0.0,
            "standard_cost": 272.8,
            "last_revision_date": "20031031",
            "ncm_ipi_position": "85444200",
        },
        "structure": {
            "root": {
                "code": "90260148",
                "description": "CHICOTE DE LIGACAO",
                "type": "PA",
                "unit": "MI",
                "quantity": 1,
            },
            "items": [
                {
                    "code": "50220013",
                    "description": "CB18BRAN-00368/06/15-3100-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 2.0,
                    "components": [
                        {
                            "code": "10030015",
                            "description": "CABO EPR 130ºC 18AWG BN NBR 9114",
                            "type": "MP",
                            "unit": "MT",
                            "quantity": 368.0,
                        },
                        {
                            "code": "10080031",
                            "description": "TERM. FASTON 6,30X0,80",
                            "type": "MP",
                            "unit": "PC",
                            "quantity": 1000.0,
                        },
                    ],
                },
                {
                    "code": "50220015",
                    "description": "CB18VERM-00318/06/15-3100-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 2.0,
                    "components": [
                        {
                            "code": "10030012",
                            "description": "CABO EPR 130ºC 18AWG VM NBR 9114",
                            "type": "MP",
                            "unit": "MT",
                            "quantity": 318.0,
                        },
                        {
                            "code": "10080031",
                            "description": "TERM. FASTON 6,30X0,80",
                            "type": "MP",
                            "unit": "PC",
                            "quantity": 1000.0,
                        },
                    ],
                },
            ],
            "total": 2,
        },
        "guide": {"items": [], "total": 0},
        "inspection": {"items": [], "total": 0},
    }


def test_present_product_analyser_expands_structure_and_insights():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        _sample_analyser_payload(),
        path="/products/90260148/analyser",
    )

    body = "\n".join(humanized["linhas"])

    assert "| Campo | Valor |" not in body
    assert "Destaques" in body or "Insights" in body
    assert "árvore" in body.lower() or "tabela" in body.lower()
    assert humanized["apresentacao"]["type"] == "tree"
    assert humanized["apresentacao"]["root"]["children"][0]["label"] == "50220013"


def test_build_presentation_uses_profile_table_for_analyser():
    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        _sample_analyser_payload(),
        path="/products/90260148/analyser",
    )

    assert table is not None
    assert table["type"] == "table"
    assert table["title"].startswith("Produto ")
    assert any(row.get("campo") == "Código" for row in table["rows"])


def test_build_presentation_uses_guide_table_when_analyser_has_route():
    from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
        _analyser_payload_with_guide_and_inspection,
    )

    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        _analyser_payload_with_guide_and_inspection(),
        path="/products/90260140/analyser",
    )

    assert table is not None
    assert table["type"] == "table"
    assert "Roteiro" in table["title"]
    assert any(row.get("operation_description") == "CORTAR TUBO MAIOR E MENOR" for row in table["rows"])


def test_build_tree_presentation_for_analyser():
    presenter = ExternalActionResultPresenter()

    tree = presenter.build_tree_presentation(
        _sample_analyser_payload(),
        path="/products/90260148/analyser",
    )

    assert tree is not None
    assert tree["type"] == "tree"
    assert tree["root"]["children"][0]["children"][0]["label"] == "10030015"


def test_present_product_analyser_unwraps_double_success_data_wrapper():
    presenter = ExternalActionResultPresenter()

    payload = {
        "success": True,
        "product": {
            "success": True,
            "data": {
                "success": True,
                "data": {
                    "group_code": "1008",
                    "code": "10080001",
                    "description": "TERM. BANDEIRA 6,30X0,80",
                    "type": "MP",
                    "unit": "PC",
                    "active": "S",
                    "default_warehouse": "01",
                    "last_purchase_price": 0.033,
                    "standard_cost": 0.02583,
                    "last_revision_date": "20231016",
                    "ncm_ipi_position": "85369090",
                },
            },
        },
        "structure": {"items": [], "total": 0},
        "guide": {"items": [], "total": 0},
        "inspection": {"items": [], "total": 0},
    }

    humanized = presenter.present(payload, path="/products/10080001/analyser")
    body = "\n".join(humanized["linhas"])

    assert "10080001" in body
    assert "TERM. BANDEIRA" in body
    assert "None" not in body


def test_build_text_presentation_unwraps_double_success_data_wrapper():
    presenter = ExternalActionResultPresenter()

    payload = {
        "success": True,
        "product": {
            "success": True,
            "data": {
                "success": True,
                "data": {
                    "group_code": "1008",
                    "code": "10080001",
                    "description": "TERM. BANDEIRA 6,30X0,80",
                    "type": "MP",
                    "unit": "PC",
                    "active": "S",
                    "default_warehouse": "01",
                    "last_purchase_price": 0.033,
                    "standard_cost": 0.02583,
                    "last_revision_date": "20231016",
                    "ncm_ipi_position": "85369090",
                },
            },
        },
        "structure": {"items": [], "total": 0},
        "guide": {"items": [], "total": 0},
        "inspection": {"items": [], "total": 0},
    }

    text = presenter.build_text_presentation(
        payload,
        path="/products/10080001/analyser",
    )

    assert text is not None
    assert "10080001" in text["markdown"]
    assert "TERM. BANDEIRA" in text["markdown"]
    assert "None" not in text["markdown"]


def test_build_text_presentation_includes_structure_markdown():
    presenter = ExternalActionResultPresenter()

    text = presenter.build_text_presentation(
        _sample_analyser_payload(),
        path="/products/90260148/analyser",
    )

    assert text is not None
    assert "50220013" not in text["markdown"]
    assert "Destaques" in text["markdown"] or "Pontos de atenção" in text["markdown"]
    assert "estrutura" in text["markdown"].lower()
    assert "Estrutura: 2 registro(s)" not in text["markdown"]
