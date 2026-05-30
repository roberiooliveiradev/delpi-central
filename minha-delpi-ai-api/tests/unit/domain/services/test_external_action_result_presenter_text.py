from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_build_text_presentation_from_product_payload():
    presenter = ExternalActionResultPresenter()

    text = presenter.build_text_presentation(
        {
            "product": {
                "code": "10080055",
                "description": "TERM. FASTON 4,80X0,50",
                "type": "ME",
                "unit": "UN",
            }
        },
        path="/products/{code}",
    )

    assert text is not None
    assert text["type"] == "markdown"
    assert "10080055" in text["markdown"]
    assert "TERM. FASTON" in text["markdown"]


def test_build_guide_table_uses_portuguese_column_labels():
    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        {
            "items": [
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90260123",
                    "operation_code": "01",
                    "operation_description": "EMBALAR",
                    "resource_code": "CT-19",
                    "work_center": "CT-19",
                    "setup_hours": 0.02,
                    "standard_time_hour_mil": 1,
                    "standard_time_hours_piece": 0.001,
                    "standard_time_minutes_piece": 0.06,
                    "operation_type": "1",
                    "mandatory_operation": "",
                    "mandatory_sequence": "",
                    "mandatory_report": "",
                }
            ],
            "page": 1,
            "page_size": 50,
            "total": 1,
            "total_pages": 1,
        },
        path="/products/90260123/guide",
    )

    assert table is not None
    assert table["type"] == "table"
    assert table["title"] == "Roteiro do produto"

    labels = {column["key"]: column["label"] for column in table["columns"]}

    assert labels["route_code"] == "Cód. roteiro"
    assert labels["operation_code"] == "Cód. operação"
    assert labels["operation_description"] == "Descrição operação"
    assert labels["work_center"] == "Centro de trabalho"
    assert "Route code" not in labels.values()
    assert "Operation description" not in labels.values()


def test_build_guide_table_prefers_openapi_schema_labels():
    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        {
            "items": [
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90260123",
                    "operation_code": "01",
                    "operation_description": "EMBALAR",
                    "work_center": "CT-19",
                }
            ]
        },
        path="/products/90260123/guide",
        response_schema={
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "properties": {
                                            "route_code": {
                                                "type": "string",
                                                "title": "Roteiro SG2",
                                            }
                                        }
                                    },
                                }
                            }
                        }
                    }
                }
            }
        },
    )

    labels = {column["key"]: column["label"] for column in table["columns"]}

    assert labels["route_code"] == "Roteiro SG2"


def test_present_guide_items_builds_operational_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "items": [
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90260142",
                    "operation_code": "01",
                    "operation_description": "CORTAR - MANUAL",
                    "work_center": "CT-05",
                    "bom_level": 0,
                },
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90260142",
                    "operation_code": "02",
                    "operation_description": "INSERIR TUBO ISOLANTE",
                    "work_center": "CT-08",
                    "bom_level": 0,
                },
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "50230070",
                    "operation_code": "01",
                    "operation_description": "CORTAR / DECAPAR - MAQUINA",
                    "work_center": "CT-01A",
                    "bom_level": 1,
                },
            ]
        },
        path="/products/90260142/guide",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert "90260142" in joined
    assert "CORTAR - MANUAL" in joined
    assert "INSERIR TUBO ISOLANTE" in joined
    assert "componente" in joined.lower()


def test_present_stock_items_builds_operational_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 100,
                    "available_quantity": 80,
                    "committed_quantity": 20,
                    "physical_location": "A-01",
                },
                {
                    "branch": "02",
                    "warehouse": "01",
                    "current_quantity": 50,
                    "available_quantity": 50,
                    "committed_quantity": 0,
                    "physical_location": "B-02",
                },
            ]
        },
        path="/products/10080055/stock",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert "10080055" in joined
    assert "80" in joined
    assert "Filial" in joined
    assert "disponível" in joined.lower()


def test_present_structure_builds_component_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "root": {
                "code": "90260142",
                "description": "CABO TESTE",
                "type": "PA",
                "unit": "UN",
                "quantity": 1,
            },
            "items": [
                {
                    "code": "50230070",
                    "description": "TERMINAL A",
                    "type": "ME",
                    "unit": "UN",
                    "quantity": 2,
                },
                {
                    "code": "10030015",
                    "description": "FIO COBRE",
                    "type": "MP",
                    "unit": "M",
                    "quantity": 1.5,
                },
            ],
            "total": 2,
        },
        path="/products/90260142/structure",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert "90260142" in joined
    assert "50230070" in joined
    assert "10030015" in joined
    assert "matéria(s)-prima" in joined.lower() or "matéria-prima" in joined.lower()


def test_present_inspection_nested_builds_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "items": [
                {
                    "product_code": "90260142",
                    "bom_level": 0,
                    "has_inspection": True,
                    "header": {
                        "description": "Plano principal",
                        "inspection_type": "D",
                    },
                    "measurable_tests": [
                        {
                            "test_code": "T01",
                            "sequence": 1,
                            "unit": "mm",
                            "nominal_value": 10,
                            "lower_spec_limit": 9.5,
                            "upper_spec_limit": 10.5,
                        }
                    ],
                    "textual_tests": [{"test_code": "T02", "sequence": 2, "text": "Visual"}],
                }
            ]
        },
        path="/products/90260142/inspection",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert "90260142" in joined
    assert "Plano principal" in joined
    assert "dimensional" in joined.lower()
    assert "T01" in joined


def test_present_inspection_flat_rows_builds_summary():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "items": [
                {
                    "inspection_type": "Dimensional",
                    "sequence": 1,
                    "characteristic": "Comprimento",
                    "specification": "10 mm +/- 0,5",
                },
                {
                    "inspection_type": "Visual",
                    "sequence": 2,
                    "characteristic": "Acabamento",
                },
            ]
        },
        path="/products/90260142/inspection",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert "Comprimento" in joined
    assert "Acabamento" in joined


def test_present_guide_path_avoids_sql_title():
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "items": [
                {
                    "operation_code": "10",
                    "operation_description": "Montagem principal",
                    "bom_level": 0,
                    "product_code": "90260142",
                    "work_center": "C01",
                }
            ]
        },
        path="/products/90260142/guide",
    )

    joined = "\n".join(humanized.get("linhas") or [])

    assert humanized.get("titulo") != "Consulta SQL"
    assert "90260142" in joined
    assert "Montagem principal" in joined
