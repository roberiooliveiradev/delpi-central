"""Testes de desempate de provider e seleção de produto pós-registry (DOCIE Fase 9)."""

from app.application.services.external_actions.external_action_operational_route_selection_service import (
    ExternalActionOperationalRouteSelectionService,
)
from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.application.services.external_actions.external_action_route_selection_service import (
    ExternalActionRouteSelectionService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent


class _FakeRepository:
    def __init__(self, actions: list[dict] | None = None):
        self._actions = actions or []

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        matches = list(self._actions)[:limit]

        if allowed:
            matches = [
                action
                for action in matches
                if str(action.get("actionId")) in allowed
            ]

        return matches

    def list_actions(self, provider_key=None):
        return list(self._actions)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_stable_sort_by_allowed_action_ids_breaks_ties_without_score_change():
    catalog = ExternalActionProductRouteCatalogService(_FakeRepository())
    candidates = [
        {"actionId": "provider-b"},
        {"actionId": "provider-a"},
    ]

    ordered = catalog.stable_sort_by_allowed_action_ids(
        candidates,
        ["provider-a", "provider-b"],
    )

    assert [item["actionId"] for item in ordered] == ["provider-a", "provider-b"]


def test_operational_product_selection_prefers_first_allowed_provider_for_analyser():
    repository = _FakeRepository(
        [
            {
                "actionId": "api_delpi.products.get_product_analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "api_externa.products.get_product_analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    catalog = ExternalActionProductRouteCatalogService(repository)
    service = ExternalActionOperationalRouteSelectionService(catalog)

    selected = service.select_product_with_code(
        "ficha completa do produto 90260140",
        "90260140",
        allowed_action_ids=[
            "api_externa.products.get_product_analyser",
            "api_delpi.products.get_product_analyser",
        ],
        intent=ChatProductQueryIntent.ANALYSER,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "api_externa.products.get_product_analyser"


def test_product_route_selection_picks_summary_over_analyser_for_resumo():
    repository = _FakeRepository(
        [
            {
                "actionId": "summary",
                "method": "GET",
                "path": "/products/{code}/summary",
                "operationId": "get_product_summary",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
            {
                "actionId": "analyser",
                "method": "GET",
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "parametersSchema": [{"name": "code", "in": "path", "required": True}],
            },
        ]
    )
    route_selection = ExternalActionRouteSelectionService(repository)

    selected = route_selection.select_product(
        "resumo do produto 10080047",
        "10080047",
        allowed_action_ids=["summary", "analyser"],
        intent=ChatProductQueryIntent.SUMMARY,
    )

    assert selected is not None
    assert selected["arguments"]["actionId"] == "summary"
