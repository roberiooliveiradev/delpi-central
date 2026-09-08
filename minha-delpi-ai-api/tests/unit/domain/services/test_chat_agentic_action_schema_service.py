from app.domain.services.chat_agentic_action_schema_service import (
    ChatAgenticActionSchemaService,
)
from app.domain.services.chat_operational_pagination_defaults_service import (
    ChatOperationalPaginationDefaultsService,
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
            "page_size": ChatOperationalPaginationDefaultsService.agentic_example_page_size(),
        }
    }


def test_build_slim_action_preserves_when_not_to_use_within_budget():
    slim = ChatAgenticActionSchemaService.build_slim_action(
        {
            "actionId": "api_delpi.dashboard.get_dashboard_department_indicators",
            "method": "GET",
            "path": "/dashboard/department-indicators",
            "summary": "IDD do departamento com indicadores (metas e realizado)",
            "description": (
                "Nota IDD do departamento e, para cada indicador, metas e realizado "
                "no período. Texto longo adicional para forçar truncamento do slim "
                "antes do negativo se ele ficasse só no final da descrição."
            ),
            "whenNotToUse": (
                "Não use para ROL comercial, série de receita, taxa de conversão "
                "ou faturamento — prefira /commercial/rol/series."
            ),
            "parametersSchema": [],
        }
    )

    assert len(slim["description"]) <= 220
    assert "ROL comercial" in slim["description"]
    assert "/commercial/rol/series" in slim["description"]


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
