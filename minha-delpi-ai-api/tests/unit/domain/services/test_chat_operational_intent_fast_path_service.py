from app.domain.services.chat_operational_intent_fast_path_service import (
    ChatOperationalIntentFastPathService,
)
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent


def test_should_skip_llm_tool_selection_for_stock_with_code():
    assert ChatOperationalIntentFastPathService.should_skip_llm_tool_selection(
        "estoque do produto 10090016",
    )


def test_should_not_skip_llm_tool_selection_without_code():
    assert not ChatOperationalIntentFastPathService.should_skip_llm_tool_selection(
        "como funciona o estoque?",
    )


def test_resolve_operational_fast_path_stock():
    code, intent = ChatOperationalIntentFastPathService.resolve_operational_fast_path(
        "estoque do produto 10090016",
    )

    assert code == "10090016"
    assert intent == ChatProductQueryIntent.STOCK
