from unittest.mock import MagicMock, patch

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


def test_intent_router_explicit_web_request():
    route = ChatIntentRouterService.classify(
        "pesquise na web sobre Delpi Conexões Elétricas",
        allowed_action_ids=["action-1"],
    )

    assert route.requires_web is True
    assert route.decision == "web_search"


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_intent_router_public_fact_weather(_enabled):
    route = ChatIntentRouterService.classify("qual a temperatura de amanha?")

    assert route.intent == "web_search"
    assert route.requires_web is True
    assert route.decision == "web_search"


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=False)
def test_select_action_skips_product_search_for_web_phrase(_enabled):
    service = ExternalActionSelectionService(MagicMock())

    selected = service.select_action(
        "pesquise na web sobre Delpi Conexões Elétricas",
        allowed_action_ids=["api_delpi.products.search_products"],
    )

    assert selected is None


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_select_action_skips_product_search_when_web_enabled(_enabled):
    service = ExternalActionSelectionService(MagicMock())

    selected = service.select_action(
        "pesquise na web sobre Delpi Conexões Elétricas",
        allowed_action_ids=["api_delpi.products.search_products"],
    )

    assert selected is None
