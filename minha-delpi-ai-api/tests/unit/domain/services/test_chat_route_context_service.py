from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_route_context_service import ChatRouteContextService


def test_infer_purchases_segment_from_recent_tool():
    history = [
        {"role": "user", "content": "resumo do produto 10080047"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/summary",
                        },
                    }
                ]
            },
        },
    ]

    segment = ChatRouteContextService.infer_product_route_segment_from_recent_tool(history)

    assert segment == "summary"
    assert ChatRouteContextService.resolve_product_route_segment(
        "ultimas compras",
        previous_messages=history,
    ) == "purchases"
    assert (
        ChatProductQueryIntentService.resolve_product_code(
            "ultimas compras",
            previous_messages=history,
        )
        == "10080047"
    )


def test_collect_recent_metric_route_for_supplies_cpv():
    history = [
        {"role": "user", "content": "qual o cpv"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/supplies/cpv",
                        },
                    }
                ]
            },
        },
    ]

    route = ChatRouteContextService.collect_recent_metric_route(history)

    assert route is not None
    assert route.kind == "supplies"
    assert route.path_token == "cpv"
