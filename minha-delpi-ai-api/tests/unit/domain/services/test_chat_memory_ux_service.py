"""Testes — ChatMemoryUxService (Fase 8)."""

from __future__ import annotations

from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_memory_ux_service import ChatMemoryUxService


def test_build_context_chips_topic_and_task():
    chips = ChatMemoryUxService.build_context_chips(
        {
            "conversationState": {
                "activeTopic": "playbook memória",
                "activeTask": {
                    "type": "playbook_creation",
                    "label": "playbook",
                    "objective": "memória e contexto",
                },
            },
        },
    )

    kinds = {chip["kind"] for chip in chips}

    assert "topic" in kinds
    assert "task" in kinds


def test_memory_introspection_direct_answer():
    answer = ChatMemoryUxService.build_direct_answer(
        "Quais informações você está usando?",
        {
            "lastEntities": {"productCode": "10080001"},
            "conversationState": {"activeTopic": "estoque"},
            "preferencesAppliedLabels": ["Respostas curtas"],
        },
    )

    assert answer is not None
    assert "10080001" in answer
    assert "estoque" in answer.lower()


def test_pipeline_includes_topic_chip():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="continue o playbook",
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "contextSnapshot": {
                        "conversationState": {
                            "activeTopic": "playbook",
                            "activeTask": {
                                "type": "playbook_creation",
                                "label": "playbook",
                                "status": "in_progress",
                            },
                        },
                    },
                },
            },
        ],
    )

    kinds = {chip.get("kind") for chip in ChatConversationMemoryService.build_context_chips(snapshot)}

    assert "topic" in kinds or "task" in kinds
