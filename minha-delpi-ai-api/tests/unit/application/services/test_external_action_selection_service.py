from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self.actions


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
