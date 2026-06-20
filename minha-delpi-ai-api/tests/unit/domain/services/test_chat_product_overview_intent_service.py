from app.domain.services.chat_product_overview_intent_service import (
    ChatProductOverviewIntentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


def test_me_fale_do_produto_is_overview():
    assert ChatProductOverviewIntentService.is_product_overview_message(
        "me fale do produto 90260114"
    )


def test_estoque_is_not_overview():
    assert not ChatProductOverviewIntentService.is_product_overview_message("estoque")


def test_detect_maps_overview_to_analyser_intent():
    assert (
        ChatProductQueryIntentService.detect("me fale do produto 90260114")
        == ChatProductQueryIntent.ANALYSER
    )


def test_should_force_llm_with_successful_tool():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {"ok": True, "path": "/products/90260114"},
        }
    ]

    assert ChatProductOverviewIntentService.should_force_llm_synthesis(
        "me fale do produto 90260114",
        tool_calls,
    )


def test_overview_policy_varies_by_response_mode():
    assert (
        ChatProductOverviewIntentService._overview_policy_for_mode("fast")
        == "product-overview-fast.md"
    )
    assert (
        ChatProductOverviewIntentService._overview_policy_for_mode("normal")
        == "product-overview.md"
    )
    assert (
        ChatProductOverviewIntentService._overview_policy_for_mode("thinker")
        == "product-overview-thinker.md"
    )
