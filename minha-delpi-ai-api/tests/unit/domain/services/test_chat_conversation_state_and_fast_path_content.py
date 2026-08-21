"""Contrato de patterns em conversation_state e fast_path."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_conversation_state_service import ChatConversationStateService
from app.domain.services.chat_fast_path_service import ChatFastPathService


def test_conversation_state_patterns_compile():
    for key in ("topicChange", "continuation", "resume", "correction", "sensitive"):
        source = ChatAssistantContentService.get(
            "conversation_state", "patterns", key
        )
        assert source, f"missing conversation_state.patterns.{key}"

    assert ChatAssistantContentService.list(
        "conversation_state", "clearContextPhrases"
    )


def test_conversation_state_topic_and_continuation():
    snapshot = ChatConversationStateService.apply_pre_turn(
        {},
        message="agora vamos falar de outro assunto",
    )
    assert snapshot.get("preferencesTopicChanged") is True

    cont = ChatConversationStateService.apply_pre_turn(
        {"conversationState": {"activeTask": {"type": "sql_task", "label": "SQL"}}},
        message="continue",
    )
    assert cont.get("continuationRequested") is True


def test_fast_path_patterns_compile():
    for key in ("knowledgeHint", "operationalHint", "refinementHint"):
        assert ChatAssistantContentService.get("fast_path", "patterns", key)


def test_fast_path_blocks_operational_hints():
    assert ChatFastPathService.should_use("ok") is True
    assert ChatFastPathService.should_use("estoque do produto") is False
    assert ChatFastPathService.should_use("filial 01") is False
