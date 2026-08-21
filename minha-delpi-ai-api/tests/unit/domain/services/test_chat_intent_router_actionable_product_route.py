"""Router operational gate must honor registry actionable predicates — not only keywords."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_intent_router.chat_intent_router_heuristics_service import (  # noqa: E402
    ChatIntentRouterHeuristicsService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService  # noqa: E402
from app.domain.services.chat_operational_ambiguity_service import (  # noqa: E402
    ChatOperationalAmbiguityService,
)
from app.domain.services.chat_turn_analysis_service import ChatTurnAnalysisService  # noqa: E402


# Phrases that match routePredicates / registry but are absent from operationalKeywords.
_OUTSIDE_KEYWORD_LIST = (
    "ultimas notas fiscais do 90260148",
    "movimentacao interna do 90260148",
)


def test_looks_operational_without_operational_keywords_when_actionable_predicate_hits():
    for message in _OUTSIDE_KEYWORD_LIST:
        lowered = message.lower()
        assert not any(
            term in lowered
            for term in ChatIntentRouterHeuristicsService.product_router_terms(
                "operationalKeywords"
            )
        ), message
        assert ChatIntentRouterHeuristicsService.looks_operational(message) is True, message


def test_ambiguity_cleared_when_actionable_registry_predicate_hits():
    for message in _OUTSIDE_KEYWORD_LIST:
        ambiguous, candidates = ChatOperationalAmbiguityService.resolve(
            message,
            {"productCode": "90260148"},
        )
        assert ambiguous is False, message
        assert candidates == (), message


def test_ambiguity_still_open_for_bare_product_code_scope():
    ambiguous, candidates = ChatOperationalAmbiguityService.resolve(
        "produto 90260148",
        {"productCode": "90260148"},
    )
    assert ambiguous is True
    assert candidates


def test_router_classifies_actionable_product_routes_without_turn_analysis():
    for message in _OUTSIDE_KEYWORD_LIST:
        route = ChatIntentRouterService.classify(
            message,
            allowed_action_ids=["inbound-invoice", "outbound-invoice", "action-1"],
        )
        assert route.intent == "operational_query", message
        assert route.decision == "operational_action", message
        assert route.ambiguous is False, message
        assert route.requires_tool is True, message
        assert route.reason != "no_clear_intent", message
        assert (
            ChatTurnAnalysisService.should_analyze(
                response_mode="normal",
                heuristic_intent=route.intent,
                heuristic_decision=route.decision,
                heuristic_reason=route.reason,
                heuristic_confidence=route.confidence,
            )
            is False
        ), message
