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
