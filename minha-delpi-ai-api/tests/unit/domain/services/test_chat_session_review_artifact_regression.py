from app.domain.services.chat_conversation_message_search_service import (
    ChatConversationMessageSearchService,
)


def test_session_review_false_for_artifact_question():
    assert not ChatConversationMessageSearchService.is_session_review_request(
        "o que me diz sobre os itens?"
    )


def test_session_review_true_for_conversation_meta():
    assert ChatConversationMessageSearchService.is_session_review_request(
        "o que me diz sobre a conversa?"
    )
