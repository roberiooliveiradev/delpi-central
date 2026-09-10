from app.infrastructure.external_actions.openapi_action_importer import OpenApiActionImporter


def test_importer_folds_when_to_use_into_description_and_metadata():
    schema = {
        "openapi": "3.0.0",
        "paths": {
            "/items/{code}": {
                "get": {
                    "operationId": "get_item_overview",
                    "tags": ["items"],
                    "summary": "Overview",
                    "description": "Light overview.",
                    "x-delpi": {
                        "locale": {
                            "pt-BR": {
                                "summary": "Visão geral",
                                "description": "Visão geral do item.",
                                "whenToUse": "Use para «descrição» ou «cadastro».",
                                "whenNotToUse": "Não use para «estoque».",
                            }
                        }
                    },
                }
            }
        },
    }
    actions = OpenApiActionImporter().import_actions("ext-api", schema)
    assert len(actions) == 1
    action = actions[0]
    assert "«descrição»" in (action.get("description") or "")
    assert action.get("when_to_use")
    assert (action.get("delpi_metadata") or {}).get("whenToUse")
    assert "«descrição»" in str(action["delpi_metadata"]["whenToUse"])


def test_importer_materializes_ref_titles_for_column_labels():
    from app.domain.services.external_actions.external_action_column_label_service import (
        ExternalActionColumnLabelService,
    )

    schema = {
        "openapi": "3.0.0",
        "paths": {
            "/products/{code}/stock": {
                "get": {
                    "operationId": "get_product_stock",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "items": {
                                                "type": "array",
                                                "items": {
                                                    "$ref": "#/components/schemas/StockItem"
                                                },
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "StockItem": {
                    "type": "object",
                    "properties": {
                        "warehouse": {"type": "string", "title": "Armazém"},
                        "available_quantity": {
                            "type": "number",
                            "title": "Qtd. disponível",
                        },
                    },
                }
            }
        },
    }

    actions = OpenApiActionImporter().import_actions("api-delpi", schema)
    assert actions
    labels = ExternalActionColumnLabelService().resolve_schema_labels(
        actions[0]["response_schema"]
    )
    assert labels["warehouse"] == "Armazém"
    assert labels["available_quantity"] == "Qtd. disponível"

