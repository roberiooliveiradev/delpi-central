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
