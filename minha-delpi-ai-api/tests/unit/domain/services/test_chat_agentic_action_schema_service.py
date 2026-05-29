from app.domain.services.chat_agentic_action_schema_service import (
    ChatAgenticActionSchemaService,
)


def test_build_slim_action_includes_description_parameters_and_examples():
    slim = ChatAgenticActionSchemaService.build_slim_action(
        {
            "actionId": "api_delpi.products.get_product_stock",
            "method": "GET",
            "path": "/products/{code}/stock",
            "summary": "Consulta estoque do produto",
            "description": "Retorna saldo por filial e armazém.",
            "parametersSchema": [
                {
                    "name": "code",
                    "in": "path",
                    "required": True,
                    "description": "Código do produto",
                },
                {
                    "name": "branch",
                    "in": "query",
                    "schema": {"type": "string", "example": "02"},
                },
                {
                    "name": "page_size",
                    "in": "query",
                    "schema": {"type": "integer"},
                },
            ],
        }
    )

    assert slim["actionId"] == "api_delpi.products.get_product_stock"
    assert slim["method"] == "GET"
    assert "Consulta estoque" in slim["description"]
    assert slim["parameters"][0]["example"] == "10080022"
    assert slim["parameters"][1]["example"] == "02"
    assert slim["exampleArguments"] == {
        "parameters": {
            "code": "10080022",
            "branch": "02",
            "page_size": 50,
        }
    }


def test_format_planner_catalog_returns_json_array():
    payload = ChatAgenticActionSchemaService.format_planner_catalog(
        [
            {
                "actionId": "stock-action",
                "description": "Estoque",
                "parameters": [],
            }
        ]
    )

    assert '"actionId": "stock-action"' in payload
    assert '"description": "Estoque"' in payload
