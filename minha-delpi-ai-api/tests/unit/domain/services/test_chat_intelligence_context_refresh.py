from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_conversation_message_search_service import (
    ChatConversationMessageSearchService,
)
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_operational_retry_message_service import (
    ChatOperationalRetryMessageService,
)

configure_domain_infrastructure_ports()


def test_fast_path_blocks_tente_novamente():
    assert ChatFastPathService.should_use("tente novamente") is False


def test_retry_is_operational_follow_up():
    assert ChatFollowUpIntentService.is_retry_or_continue_request("tente novamente")
    assert ChatFollowUpIntentService.is_operational_follow_up("tente novamente")
    assert ChatFollowUpIntentService.follow_up_type("tente novamente") == "retry"


def test_retry_rewrites_to_last_operational_message():
    rewritten, did = ChatOperationalRetryMessageService.rewrite_if_needed(
        "tente novamente",
        [
            {"role": "user", "content": "qual o estoque 10080047"},
            {
                "role": "assistant",
                "content": "Dados operacionais exigem um agente",
            },
        ],
    )
    assert did is True
    assert "10080047" in rewritten


def test_message_search_triggers_on_explicit_recall():
    result = ChatConversationMessageSearchService.search(
        message="releia a conversa o que eu pedi",
        previous_messages=[
            {"role": "user", "content": "gere um texto formal em tabela"},
            {"role": "assistant", "content": "Segue o texto..."},
        ],
        response_mode="normal",
    )
    assert result["triggered"] is True
    assert result["hitCount"] >= 1
    assert "Evidências" in result["promptBlock"] or "conversa" in result["promptBlock"].lower()
