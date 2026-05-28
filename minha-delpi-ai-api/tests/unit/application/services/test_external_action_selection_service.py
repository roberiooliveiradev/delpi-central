from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
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
