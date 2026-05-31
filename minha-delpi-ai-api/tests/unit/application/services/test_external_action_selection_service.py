from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.infrastructure.config.settings import Settings


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self.actions

    def list_actions(self):
        return self.actions


def test_select_stock_without_code_does_not_use_semantic_fallback():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "commercial-rol",
                    "method": "GET",
                    "path": "/commercial/new-business-rol-pct",
                    "operationId": "get_new_business_rol_pct",
                    "summary": "ROL novos negocios",
                    "selectionScore": 0.99,
                },
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Product stock",
                    "selectionScore": 0.1,
                },
            ]
        )
    )

    selected = service.select_action(
        "estoque do produto",
        allowed_action_ids=["commercial-rol", "stock-action"],
    )

    assert selected is None


def test_select_stock_action_uses_code_from_conversation_context():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "product_stock",
                    "summary": "Product stock",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
                {
                    "actionId": "analyser-action",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "product_analyser",
                    "summary": "Product analyser",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "busque o estoque desse produto",
        allowed_action_ids=["stock-action", "analyser-action"],
        conversation_context="assistant: Produto 10080047: TERM. PINO RETO.",
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080047"


def test_select_product_action_normalizes_masked_code():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "analyser-action",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "product_analyser",
                    "summary": "Product analyser",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "descrição do produto 10.080.055",
        allowed_action_ids=["analyser-action"],
    )

    assert selected is not None
    assert selected["arguments"]["parameters"]["code"] == "10080055"


def test_select_product_search_by_group_not_analyser():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "search",
                    "method": "GET",
                    "path": "/products/search",
                    "operationId": "search_products",
                    "summary": "Busca de produtos",
                    "parametersSchema": [
                        {"name": "group_code"},
                        {"name": "page_size"},
                    ],
                },
                {
                    "actionId": "analyser",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "get_product_analyser",
                    "summary": "Analisador",
                    "parametersSchema": [{"name": "code"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "busque 3 produtos do grupo 1008",
        allowed_action_ids=["search", "analyser"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "search"
    assert selected["arguments"]["parameters"]["group_code"] == "1008"
    assert selected["arguments"]["parameters"]["page_size"] == 3


def test_select_lmp_by_sale_number_prefers_detail_route():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "list-lmps",
                    "method": "GET",
                    "path": "/engineering/lmps",
                    "operationId": "list_lmps",
                    "summary": "Listar LMPs",
                    "parametersSchema": [
                        {"name": "page"},
                        {"name": "page_size"},
                    ],
                },
                {
                    "actionId": "get-lmp",
                    "method": "GET",
                    "path": "/engineering/lmps/{sale_number}",
                    "operationId": "get_lmp_by_sale_number",
                    "summary": "Detalhe da LMP por ordem de venda",
                    "parametersSchema": [
                        {"name": "sale_number", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "detalhe da LMP da OV 123456",
        allowed_action_ids=["list-lmps", "get-lmp"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "get-lmp"
    assert selected["arguments"]["parameters"]["sale_number"] == "123456"


def test_select_supplies_stock_value_for_aggregate_question():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "product-stock",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Estoque do produto por filial",
                    "parametersSchema": [{"name": "code"}],
                },
                {
                    "actionId": "supplies-stock-value",
                    "method": "GET",
                    "path": "/supplies/stock-value",
                    "operationId": "get_supplies_stock_value",
                    "summary": "Valor total de estoque (suprimentos)",
                    "parametersSchema": [{"name": "top_limit"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "qual o valor total de estoque da empresa?",
        allowed_action_ids=["product-stock", "supplies-stock-value"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "supplies-stock-value"


def test_generic_fallback_returns_none_without_semantic_score():
    """Sem ranker semântico, fallback genérico não deve selecionar action aleatória."""
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "depreciation",
                    "method": "GET",
                    "path": "/production/depreciation_pct",
                    "operationId": "get_depreciation_pct",
                    "summary": "Depreciação % ROL",
                    "parametersSchema": [],
                },
                {
                    "actionId": "stock-value",
                    "method": "GET",
                    "path": "/supplies/stock-value",
                    "operationId": "get_supplies_stock_value",
                    "summary": "Valor total estoque",
                    "parametersSchema": [],
                },
            ]
        )
    )

    selected = service.select_action(
        "o que mais pode me dizer sobre um produto?",
        allowed_action_ids=["depreciation", "stock-value"],
    )

    assert selected is None


def test_monte_query_does_not_auto_select_sql_action():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "sql-action",
                    "method": "POST",
                    "path": "/data/sql",
                    "operationId": "execute_sql",
                    "summary": "Executar SQL",
                    "parametersSchema": [{"name": "query"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "monte uma query que liste os produtos que vão ser produzidos hoje",
        allowed_action_ids=["sql-action"],
    )

    assert selected is None


def test_production_schedule_question_does_not_select_product_search():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "search-products",
                    "method": "GET",
                    "path": "/products/search",
                    "operationId": "search_products",
                    "summary": "Buscar produtos",
                    "parametersSchema": [
                        {"name": "description"},
                        {"name": "page"},
                        {"name": "page_size"},
                    ],
                },
                {
                    "actionId": "sql-action",
                    "method": "POST",
                    "path": "/data/sql",
                    "operationId": "execute_sql",
                    "summary": "Executar SQL",
                    "parametersSchema": [{"name": "query"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "quais produtos serão produzidos hoje?",
        allowed_action_ids=["search-products", "sql-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sql-action"
    assert "SC2010" in selected["arguments"]["body"]["sql"]
    assert "search" not in selected["arguments"]["actionId"]


def test_execute_query_selects_sql_action():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "sql-action",
                    "method": "POST",
                    "path": "/data/sql",
                    "operationId": "execute_sql",
                    "summary": "Executar SQL",
                    "parametersSchema": [{"name": "query"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "execute essa consulta no banco",
        allowed_action_ids=["sql-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "sql-action"


def test_comparison_request_does_not_select_structure_action():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "product-structure",
                    "method": "GET",
                    "path": "/products/{code}/structure",
                    "operationId": "get_product_structure",
                    "summary": "Estrutura do produto",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "compare as duas estruturas e traga insights",
        allowed_action_ids=["product-structure"],
        conversation_context=(
            "user: estrutura do 90260077\n"
            "user: estrutura do 90260088\n"
            "assistant: Estrutura do produto 90260088"
        ),
    )

    assert selected is None


def test_select_stock_refinement_reuses_product_and_branch():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Product stock",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                    ],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto 10080022",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                            "actionId": "get_product_stock",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "filtre filial 02",
        allowed_action_ids=["stock-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080022"
    assert selected["arguments"]["parameters"]["branch"] == "02"
    assert "filial 02" in selected["reason"]


def test_select_stock_refinement_maps_warehouse_to_location():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Product stock",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                        {"name": "location", "in": "query"},
                    ],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                            "actionId": "get_product_stock",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "filtre filial 02 armazém 01",
        allowed_action_ids=["stock-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["parameters"]["branch"] == "02"
    assert selected["arguments"]["parameters"]["location"] == "01"


def test_select_stock_refinement_with_unresolved_path_template():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Product stock",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                    ],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto 10080022",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "stock-action",
                            "parameters": {"code": "10080022", "page": 1, "page_size": 50},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/{code}/stock",
                            "actionId": "stock-action",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "filtre filial 02",
        allowed_action_ids=["stock-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["parameters"]["code"] == "10080022"
    assert selected["arguments"]["parameters"]["branch"] == "02"


def test_select_stock_refinement_prefers_previous_action_provider():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "api_delpi.products.get_product_stock",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Product stock",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                    ],
                },
                {
                    "actionId": "transforma_mais.products.stock_products_code_stock_get",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "stock_products_code_stock_get",
                    "summary": "Stock transforma",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                    ],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto 10080022",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                            "actionId": "api_delpi.products.get_product_stock",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "filtre filial 02",
        allowed_action_ids=[
            "api_delpi.products.get_product_stock",
            "transforma_mais.products.stock_products_code_stock_get",
        ],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_delpi.products.get_product_stock"
    assert selected["arguments"]["parameters"]["branch"] == "02"


def test_select_product_summary_not_analyser():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "summary-action",
                    "method": "GET",
                    "path": "/products/{code}/summary",
                    "operationId": "get_product_summary",
                    "summary": "Resumo do produto",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
                {
                    "actionId": "analyser-action",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "get_product_analyser",
                    "summary": "Analisador do produto",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "resumo do produto 10080047",
        allowed_action_ids=["summary-action", "analyser-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "summary-action"
    assert selected["arguments"]["parameters"]["code"] == "10080047"


def test_select_stock_follow_up_uses_last_product_from_context():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Estoque",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
            ]
        )
    )

    selected = service.select_action(
        "estoque do produto",
        allowed_action_ids=["stock-action"],
        conversation_context=(
            "assistant: Produto 10080047: A\nassistant: Produto 10080055: B"
        ),
    )

    assert selected is not None
    assert selected["arguments"]["parameters"]["code"] == "10080055"


def test_select_stock_for_shorthand_code_after_previous_stock():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "operationId": "get_product_stock",
                    "summary": "Estoque",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
            ]
        )
    )

    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080047/stock"},
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "e do 10080055?",
        allowed_action_ids=["stock-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080055"


def test_select_product_full_analyser_not_summary():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "summary-action",
                    "method": "GET",
                    "path": "/products/{code}/summary",
                    "operationId": "get_product_summary",
                    "summary": "Resumo",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
                {
                    "actionId": "analyser-action",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "get_product_analyser",
                    "summary": "Analisador",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
            ]
        )
    )

    selected = service.select_action(
        "ficha completa do produto 10080047",
        allowed_action_ids=["summary-action", "analyser-action"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "analyser-action"


def test_select_department_kpi_refinement_with_branch():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "commercial-billing",
                    "method": "GET",
                    "path": "/commercial/billing",
                    "operationId": "get_commercial_billing",
                    "summary": "Faturamento comercial",
                    "parametersSchema": [
                        {"name": "branch", "in": "query"},
                        {"name": "start_date", "in": "query"},
                        {"name": "end_date", "in": "query"},
                    ],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "faturamento comercial"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/billing",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "filtre filial 02",
        allowed_action_ids=["commercial-billing"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "commercial-billing"
    assert selected["arguments"]["parameters"]["branch"] == "02"


def test_select_parents_follow_up_after_structure():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "structure-action",
                    "method": "GET",
                    "path": "/products/{code}/structure",
                    "operationId": "get_product_structure",
                    "summary": "Estrutura",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
                {
                    "actionId": "parents-action",
                    "method": "GET",
                    "path": "/products/{code}/parents",
                    "operationId": "get_product_parents",
                    "summary": "Pais",
                    "parametersSchema": [{"name": "code", "in": "path", "required": True}],
                },
            ]
        )
    )

    history = [
        {"role": "user", "content": "estrutura do produto 10080047"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/structure",
                        },
                    }
                ]
            },
        },
    ]

    selected = service.select_action(
        "e os pais desse produto",
        allowed_action_ids=["structure-action", "parents-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "parents-action"
    assert selected["arguments"]["parameters"]["code"] == "10080047"


def test_select_financial_rol_for_month_question():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "financial-rol",
                    "method": "GET",
                    "path": "/financial/rol",
                    "operationId": "get_rol",
                    "summary": "ROL financeiro",
                    "parametersSchema": [
                        {"name": "start_date", "in": "query"},
                        {"name": "end_date", "in": "query"},
                    ],
                },
                {
                    "actionId": "commercial-rol-series",
                    "method": "GET",
                    "path": "/commercial/rol/series",
                    "operationId": "get_commercial_rol_series",
                    "summary": "Série de ROL comercial",
                    "parametersSchema": [
                        {"name": "granularity", "in": "query", "required": True},
                        {"name": "start_date", "in": "query"},
                        {"name": "end_date", "in": "query"},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "rol do mes de marco",
        allowed_action_ids=["financial-rol", "commercial-rol-series"],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "financial-rol"
    assert selected["arguments"]["parameters"]["start_date"] == "01-03-2026"
    assert selected["arguments"]["parameters"]["end_date"] == "31-03-2026"


def test_build_date_branch_parameters_infers_granularity_for_series():
    service = ExternalActionSelectionService(FakeRepository([]))

    parameters = service._build_date_branch_parameters(
        {
            "parametersSchema": [
                {"name": "granularity", "in": "query", "required": True},
                {"name": "start_date", "in": "query"},
            ],
        },
        "rol do mes de marco",
    )

    assert parameters["granularity"] == "month"
    assert parameters["start_date"]


def test_select_product_search_when_description_not_in_structure_history():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "search-products",
                    "method": "GET",
                    "path": "/products/search",
                    "operationId": "search_products",
                    "parametersSchema": [
                        {"name": "description", "in": "query"},
                        {"name": "page_size", "in": "query"},
                    ],
                },
                {
                    "actionId": "structure-action",
                    "method": "GET",
                    "path": "/products/{code}/structure",
                    "operationId": "get_product_structure",
                    "parametersSchema": [{"name": "code", "in": "path"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
        allowed_action_ids=["search-products", "structure-action"],
        previous_messages=[],
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "search-products"
    assert "term" in selected["arguments"]["parameters"]["description"].lower()


def test_select_product_detail_from_structure_description_history():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "analyser-action",
                    "method": "GET",
                    "path": "/products/{code}/analyser",
                    "operationId": "get_product_analyser",
                    "parametersSchema": [{"name": "code", "in": "path"}],
                },
                {
                    "actionId": "structure-action",
                    "method": "GET",
                    "path": "/products/{code}/structure",
                    "operationId": "get_product_structure",
                    "parametersSchema": [{"name": "code", "in": "path"}],
                },
            ]
        )
    )

    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260143/structure",
                            "presentation": {
                                "type": "tree",
                                "root": {
                                    "id": "10080109",
                                    "label": "10080109",
                                    "subtitle": "TERM. FASTON 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO UL ROHS",
                                },
                            },
                        },
                    }
                ]
            },
        }
    ]

    selected = service.select_action(
        "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
        allowed_action_ids=["analyser-action", "structure-action"],
        previous_messages=history,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "analyser-action"
    assert selected["arguments"]["parameters"]["code"] == "10080109"


def test_select_action_skips_catalog_for_technical_description_guidance():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "search-products",
                    "method": "GET",
                    "path": "/products/search",
                    "operationId": "search_products",
                    "parametersSchema": [{"name": "description", "in": "query"}],
                },
            ]
        )
    )

    selected = service.select_action(
        "como descrever um terminal?",
        allowed_action_ids=["search-products"],
    )

    assert selected is None


def test_select_metric_refinement_uses_path_token_not_semantic_candidates():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "commercial-branch",
                    "method": "GET",
                    "path": "/commercial/branch_rol_target_pct",
                    "operationId": "get_branch_rol_target_pct",
                    "summary": "ROL filial",
                    "parametersSchema": [{"name": "branch", "in": "query"}],
                },
                {
                    "actionId": "supplies-cpv",
                    "method": "GET",
                    "path": "/supplies/cpv",
                    "operationId": "get_supplies_cpv",
                    "summary": "CPV",
                    "parametersSchema": [{"name": "branch", "in": "query"}],
                },
                {
                    "actionId": "supplies-stock-value",
                    "method": "GET",
                    "path": "/supplies/stock-value",
                    "operationId": "get_supplies_stock_value",
                    "summary": "Valor estoque",
                    "parametersSchema": [{"name": "branch", "in": "query"}],
                },
            ]
        )
    )

    cpv_history = [
        {"role": "user", "content": "qual o cpv"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/cpv"},
                    }
                ]
            },
        },
    ]
    stock_value_history = [
        {"role": "user", "content": "qual o valor total de estoque da empresa"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/stock-value"},
                    }
                ]
            },
        },
    ]

    cpv_selected = service.select_action(
        "filtre filial 02",
        allowed_action_ids=[
            "commercial-branch",
            "supplies-cpv",
            "supplies-stock-value",
        ],
        previous_messages=cpv_history,
    )
    stock_selected = service.select_action(
        "filial 01",
        allowed_action_ids=[
            "commercial-branch",
            "supplies-cpv",
            "supplies-stock-value",
        ],
        previous_messages=stock_value_history,
    )

    assert cpv_selected is not None
    assert cpv_selected["arguments"]["actionId"] == "supplies-cpv"
    assert cpv_selected["arguments"]["parameters"]["branch"] == "02"

    assert stock_selected is not None
    assert stock_selected["arguments"]["actionId"] == "supplies-stock-value"
    assert stock_selected["arguments"]["parameters"]["branch"] == "01"


def test_listar_nc_5s_does_not_select_product_search():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "search-description",
                    "method": "GET",
                    "path": "/products/search/description",
                    "operationId": "search_products_by_description",
                    "parametersSchema": [{"name": "description", "in": "query"}],
                }
            ]
        )
    )

    selected = service.select_action(
        "listar nc 5s operacional",
        allowed_action_ids=["search-description"],
    )

    assert selected is None


def test_select_suppliers_prefers_api_externa_when_configured(monkeypatch):
    from app.domain.services.chat_web_search_intent_service import (
        ChatWebSearchIntentService,
    )

    monkeypatch.setenv("CHAT_PREFER_API_EXTERNA_PROVIDER", "true")
    Settings.CHAT_PREFER_API_EXTERNA_PROVIDER = True
    monkeypatch.setattr(
        ChatWebSearchIntentService,
        "blocks_external_action_selection",
        lambda message: False,
    )

    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "api_delpi.products.suppliers_products_code_suppliers_get",
                    "method": "GET",
                    "path": "/products/{code}/suppliers",
                    "operationId": "suppliers_products_code_suppliers_get",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
                {
                    "actionId": "api_externa.products.suppliers_products_code_suppliers_get",
                    "method": "GET",
                    "path": "/products/{code}/suppliers",
                    "operationId": "suppliers_products_code_suppliers_get",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                    ],
                },
            ]
        )
    )

    selected = service.select_action(
        "liste os fornecedores do produto 10080001",
        allowed_action_ids=[
            "api_delpi.products.suppliers_products_code_suppliers_get",
            "api_externa.products.suppliers_products_code_suppliers_get",
        ],
    )

    assert selected is not None
    assert (
        selected["arguments"]["actionId"]
        == "api_externa.products.suppliers_products_code_suppliers_get"
    )
