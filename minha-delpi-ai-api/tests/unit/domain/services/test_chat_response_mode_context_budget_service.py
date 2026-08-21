from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_context_budget_service import (
    ChatResponseModeContextBudgetService,
)

configure_domain_infrastructure_ports()


def test_context_budget_ladder_by_mode():
    fast = ChatResponseModeContextBudgetService.resolve("fast")
    normal = ChatResponseModeContextBudgetService.resolve("normal")
    thinker = ChatResponseModeContextBudgetService.resolve("thinker")

    assert fast.history_max_messages < normal.history_max_messages
    assert normal.history_max_messages < thinker.history_max_messages
    assert fast.rag_max_chars < normal.rag_max_chars
    assert normal.rag_max_chars <= thinker.rag_max_chars
    assert fast.message_search_max_hits < thinker.message_search_max_hits
    assert fast.max_multi_actions_per_turn == 1
    assert normal.max_multi_actions_per_turn >= 2
    assert thinker.max_multi_actions_per_turn >= normal.max_multi_actions_per_turn


def test_history_keep_alias():
    assert ChatResponseModeContextBudgetService.history_keep("rápida") == 4
    assert ChatResponseModeContextBudgetService.history_keep("pensador") == 20


def test_admin_debug_keys():
    payload = ChatResponseModeContextBudgetService.resolve("normal").as_admin_debug()

    assert payload["mode"] == "normal"
    assert payload["historyMaxMessages"] == 12
    assert "messageSearchLookbackMessages" in payload
