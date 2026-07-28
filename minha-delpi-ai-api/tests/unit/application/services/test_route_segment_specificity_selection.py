"""Regressão: segmento operacional + código ≻ catch-all productSearch / markers frouxos."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


class _FakeRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def list_actions(self, provider_key=None):
        return self.actions


_COMPETING_ACTIONS = [
    {
        "actionId": "customers-search",
        "method": "GET",
        "path": "/customers/search",
        "operationId": "search_customers",
        "summary": "Search customers",
        "parametersSchema": [
            {"name": "code", "in": "query"},
            {"name": "q", "in": "query"},
            {"name": "page", "in": "query"},
            {"name": "page_size", "in": "query"},
        ],
    },
    {
        "actionId": "products-search",
        "method": "GET",
        "path": "/products/search",
        "operationId": "search_products",
        "summary": "Search products",
        "parametersSchema": [
            {"name": "q", "in": "query"},
            {"name": "page", "in": "query"},
            {"name": "page_size", "in": "query"},
        ],
    },
    {
        "actionId": "suppliers-action",
        "method": "GET",
        "path": "/products/{code}/suppliers",
        "operationId": "get_product_suppliers",
        "summary": "Product suppliers",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
    },
    {
        "actionId": "stock-action",
        "method": "GET",
        "path": "/products/{code}/stock",
        "operationId": "get_product_stock",
        "summary": "Product stock",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
    },
    {
        "actionId": "customers-product-action",
        "method": "GET",
        "path": "/products/{code}/customers",
        "operationId": "get_product_customers",
        "summary": "Product customers",
        "parametersSchema": [{"name": "code", "in": "path", "required": True}],
    },
]


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def _select(message: str) -> dict | None:
    service = ExternalActionSelectionService(_FakeRepository(_COMPETING_ACTIONS))
    return service.select_action(
        message,
        allowed_action_ids=[action["actionId"] for action in _COMPETING_ACTIONS],
    )


def test_liste_fornecedores_do_produto_selects_product_suppliers_not_customers_search():
    selected = _select("liste os fornecedores do produto 10080001")

    assert selected is not None
    assert selected["arguments"]["actionId"] == "suppliers-action"
    assert selected["arguments"]["parameters"]["code"] == "10080001"
    assert "customers-search" != selected["arguments"]["actionId"]


def test_liste_estoque_do_produto_selects_stock_not_product_search():
    selected = _select("liste o estoque do produto 10080001")

    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080001"


def test_liste_clientes_do_produto_selects_product_customers_not_customers_search():
    selected = _select("liste os clientes do produto 10080001")

    assert selected is not None
    assert selected["arguments"]["actionId"] == "customers-product-action"
    assert selected["arguments"]["parameters"]["code"] == "10080001"


def test_busque_produtos_por_descricao_still_uses_product_search():
    selected = _select("busque produtos cabo pp")

    assert selected is not None
    assert selected["arguments"]["actionId"] == "products-search"


def test_agora_fornecedores_uses_code_from_conversation_context():
    service = ExternalActionSelectionService(_FakeRepository(_COMPETING_ACTIONS))
    selected = service.select_action(
        "agora fornecedores",
        allowed_action_ids=[action["actionId"] for action in _COMPETING_ACTIONS],
        conversation_context="assistant: Produto 10080001: ITEM TESTE.",
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "suppliers-action"
    assert selected["arguments"]["parameters"]["code"] == "10080001"
