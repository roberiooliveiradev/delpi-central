from app.domain.services.openapi_delpi_extension_service import (
    OpenApiDelpiExtensionService,
)
from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)


def test_extract_x_delpi_from_operation():
    operation = {
        "operationId": "get_quality_nc",
        "x-delpi": {
            "entity": "quality_non_conformity",
            "shape": "paged_list",
            "presentation": {"strategy": "as_delivered"},
        },
    }

    extracted = OpenApiDelpiExtensionService.extract_from_operation(operation)

    assert extracted == {
        "entity": "quality_non_conformity",
        "shape": "paged_list",
        "presentation": {"strategy": "as_delivered"},
    }


def test_infer_delpi_metadata_from_response_example():
    operation = {
        "operationId": "get_supplies_cpv",
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "example": {
                            "meta": {
                                "entity": "supplies_cpv",
                                "shape": "scalar",
                            }
                        }
                    }
                }
            }
        },
    }

    extracted = OpenApiDelpiExtensionService.extract_from_operation(operation)

    assert extracted == {"entity": "supplies_cpv", "shape": "scalar"}


def test_importer_persists_delpi_metadata_on_action():
    schema = {
        "paths": {
            "/quality/nc": {
                "get": {
                    "operationId": "list_quality_nc",
                    "tags": ["Qualidade"],
                    "x-delpi": {
                        "entity": "quality_non_conformity",
                        "shape": "paged_list",
                    },
                }
            }
        }
    }

    actions = OpenApiActionImporter().import_actions("api-pac-quality", schema)

    assert len(actions) == 1
    assert actions[0]["delpi_metadata"] == {
        "entity": "quality_non_conformity",
        "shape": "paged_list",
    }
