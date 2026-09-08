from app.infrastructure.openapi.openapi_ref_resolver import OpenApiRefResolver
from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)
from tests.support.openapi_logistics_fixtures import load_logistics_openapi


def test_resolve_local_parameter_ref():
    schema = {
        "openapi": "3.0.3",
        "paths": {
            "/items/{id}": {
                "get": {
                    "operationId": "get_item",
                    "parameters": [{"$ref": "#/components/parameters/ItemId"}],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
        "components": {
            "parameters": {
                "ItemId": {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "example": "ABC"},
                }
            }
        },
    }

    resolved = OpenApiRefResolver.resolve_document(schema)
    param = resolved["paths"]["/items/{id}"]["get"]["parameters"][0]
    assert param["name"] == "id"
    assert param["required"] is True
    assert param["schema"]["type"] == "string"
    assert "$ref" not in param


def test_unresolved_ref_is_marked_not_raised():
    schema = {
        "openapi": "3.0.3",
        "paths": {
            "/x": {
                "get": {
                    "operationId": "get_x",
                    "parameters": [{"$ref": "#/components/parameters/Missing"}],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
        "components": {"parameters": {}},
    }
    resolved = OpenApiRefResolver.resolve_document(schema)
    param = resolved["paths"]["/x"]["get"]["parameters"][0]
    assert param.get("xDelpiUnresolvedRef") is True


def test_cycle_ref_does_not_recurse_forever():
    schema = {
        "openapi": "3.0.3",
        "paths": {
            "/cycle": {
                "get": {
                    "operationId": "get_cycle",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Node"}
                                }
                            }
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "child": {"$ref": "#/components/schemas/Node"},
                    },
                }
            }
        },
    }
    resolved = OpenApiRefResolver.resolve_document(schema)
    schema_node = resolved["paths"]["/cycle"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert schema_node["type"] == "object"
    child = schema_node["properties"]["child"]
    assert child.get("$ref") == "#/components/schemas/Node" or child.get(
        "xDelpiUnresolvedCycle"
    )


def test_all_of_merge_keeps_properties():
    schema = {
        "openapi": "3.0.3",
        "paths": {
            "/m": {
                "post": {
                    "operationId": "post_m",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {
                                            "type": "object",
                                            "properties": {"a": {"type": "string"}},
                                            "required": ["a"],
                                        },
                                        {
                                            "type": "object",
                                            "properties": {"b": {"type": "integer"}},
                                        },
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    resolved = OpenApiRefResolver.resolve_document(schema)
    body_schema = resolved["paths"]["/m"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert "a" in body_schema["properties"]
    assert "b" in body_schema["properties"]
    assert "a" in body_schema["required"]


def test_importer_materializes_logistics_shipment_id_ref():
    actions = OpenApiActionImporter().import_actions(
        "logistics-example",
        load_logistics_openapi(),
    )
    tracking = next(
        item for item in actions if item["operation_id"] == "get_shipment_tracking"
    )
    params = tracking["parameters_schema"]
    assert params
    assert params[0]["name"] == "id"
    assert params[0]["required"] is True
    assert "$ref" not in params[0]
