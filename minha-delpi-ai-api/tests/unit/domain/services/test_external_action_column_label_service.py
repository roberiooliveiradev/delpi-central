from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


def test_label_for_uses_content_dictionary():
    service = ExternalActionColumnLabelService()

    assert service.label_for("route_code") == "Cód. roteiro"
    assert service.label_for("operation_description") == "Descrição operação"


def test_label_for_prefers_openapi_schema_title():
    service = ExternalActionColumnLabelService()

    label = service.label_for(
        "route_code",
        schema_labels={"route_code": "Roteiro (OpenAPI)"},
    )

    assert label == "Roteiro (OpenAPI)"


def test_resolve_schema_labels_from_openapi_response():
    service = ExternalActionColumnLabelService()

    labels = service.resolve_schema_labels(
        {
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
                                                "title": "Cód. roteiro SG2",
                                            },
                                            "operation_code": {
                                                "type": "string",
                                                "title": "Operação",
                                            },
                                        }
                                    },
                                }
                            }
                        }
                    }
                }
            }
        }
    )

    assert labels["route_code"] == "Cód. roteiro SG2"
    assert labels["operation_code"] == "Operação"


def test_detect_guide_profile_for_sg2_schema():
    service = ExternalActionColumnLabelService()

    profile = service.detect_table_profile(
        {
            "branch": "01",
            "route_code": "01",
            "operation_code": "01",
            "operation_description": "EMBALAR",
        },
        path="/products/90260123/guide",
    )

    assert profile == "guide"


def test_preferred_columns_for_guide_profile():
    service = ExternalActionColumnLabelService()
    row = {
        "branch": "01",
        "route_code": "01",
        "product_code": "90260123",
        "operation_code": "01",
        "operation_description": "EMBALAR",
        "work_center": "CT-19",
    }

    columns = service.preferred_columns("guide", row)

    assert ("route_code", "Cód. roteiro") in columns
    assert ("operation_code", "Cód. operação") in columns
