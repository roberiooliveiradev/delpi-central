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


def test_usage_view_lists_only_user_context_item_labels():
    usage = ChatMemoryUxService.build_usage_view(
        {
            "operationalFocus": {"productCode": "90260114", "branch": "02"},
            "userContextItems": [
                {"id": "1", "label": "Política de devolução", "kind": "note"},
                {"id": "2", "label": "filial 02", "kind": "context"},
                {"id": "3", "label": "90260114", "kind": "context"},
            ],
        },
    )

    context = usage.get("userContextItems") or []

    assert "90260114" in context
    assert "filial 02" in context
    assert "Política de devolução" in context
    assert "Filial 02" not in context


def test_usage_view_context_dedupes_entity_and_manual_item():
    usage = ChatMemoryUxService.build_usage_view(
        {
            "operationalFocus": {"branch": "02"},
            "userContextItems": [
                {"id": "1", "label": "02", "kind": "branch"},
            ],
        },
    )

    context = usage.get("userContextItems") or []

    assert context.count("02") == 1


def test_memory_introspection_direct_answer():
    answer = ChatMemoryUxService.build_direct_answer(
        "Quais informações você está usando?",
        {
            "operationalFocus": {"productCode": "10080001"},
            "userContextItems": [
                {"id": "p1", "label": "10080001", "kind": "context"},
            ],
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
