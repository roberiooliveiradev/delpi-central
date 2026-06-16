"""Testes do ranking legado de rotas de produto (DOCIE Fase 4–5)."""

from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.application.services.external_actions.external_action_product_route_ranking_service import (
    ExternalActionProductRouteRankingService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent


class _FakeRepository:
    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return []


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_rank_product_actions_tie_breaks_by_allowed_action_ids_order():
    ranking = ExternalActionProductRouteRankingService()
    candidates = [
        {
            "actionId": "api_delpi.products.get_product_analyser",
            "method": "GET",
            "path": "/products/{code}/analyser",
            "operationId": "get_product_analyser",
        },
        {
            "actionId": "api_externa.products.get_product_analyser",
            "method": "GET",
            "path": "/products/{code}/analyser",
            "operationId": "get_product_analyser",
        },
    ]

    ranked = ranking.rank_product_actions(
        candidates,
        intent=ChatProductQueryIntent.ANALYSER,
        message="analise completa do produto 90260140",
        allowed_action_ids=[
            "api_externa.products.get_product_analyser",
            "api_delpi.products.get_product_analyser",
        ],
    )

    assert ranked[0]["actionId"] == "api_externa.products.get_product_analyser"


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
