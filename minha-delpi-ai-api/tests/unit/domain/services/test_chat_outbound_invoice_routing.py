from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_intent_disambiguation_service import ChatIntentDisambiguationService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_route_context_service import ChatRouteContextService


def test_segment_from_message_notas_fiscais_de_saida():
    assert (
        ChatRouteContextService.segment_from_message("notas fiscais de saída")
        == "outbound-invoice"
    )


def test_follow_up_notas_fiscais_de_saida():
    assert ChatFollowUpIntentService.is_operational_follow_up("notas fiscais de saída")


def test_classify_nf_follow_up_after_sales():
    history = [
        {"role": "user", "content": "mostre vendas do produto 90260145"},
        {
            "role": "assistant",
            "content": "Resumo",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260145/sales",
                        },
                    }
                ]
            },
        },
    ]

    route = ChatIntentRouterService.classify(
        "notas fiscais de saída",
        previous_messages=history,
        allowed_action_ids=["action-1"],
    )

    assert route.intent == "operational_query"
    assert route.is_follow_up is True
    assert route.ambiguous is False
    assert route.resolved_params == {"productCode": "90260145"}


def test_action_planning_nf_follow_up_resolves_code_from_context():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260145/sales",
                        },
                    }
                ]
            },
        },
    ]

    assert (
        ChatAnalysisIntentService.extract_product_codes_for_action_planning(
            "notas fiscais de saída",
            previous_messages=history,
        )
        == ["90260145"]
    )

    assert (
        ChatProductQueryIntentService.resolve_product_code(
            "notas fiscais de saída",
            previous_messages=history,
        )
        == "90260145"
    )


def test_disambiguation_skipped_for_explicit_nf_list():
    assert (
        ChatIntentDisambiguationService.try_build(
            "liste as notas fiscais de saída do produto 90260145",
            allowed_action_ids=["action-1"],
        )
        is None
    )
