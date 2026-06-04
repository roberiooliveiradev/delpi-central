"""Testes — ChatConversationSummarizerService (Fase 4)."""

from __future__ import annotations

from app.domain.services.chat_conversation_summarizer_service import (
    ChatConversationSummarizerService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)


def _long_history(count: int = 12):
    messages = []

    for index in range(count):
        role = "user" if index % 2 == 0 else "assistant"
        content = (
            f"Pedido {index}: consulte estoque do produto 1008000{index % 3}"
            if role == "user"
            else f"Resposta {index} com dados."
        )
        messages.append({"role": role, "content": content})

    return messages


def test_should_summarize_threshold():
    assert ChatConversationSummarizerService.should_summarize(_long_history(9)) is False
    assert ChatConversationSummarizerService.should_summarize(_long_history(10)) is True


def test_build_includes_entities_decisions_pending():
    previous = _long_history(12)
    previous.append(
        {
            "role": "user",
            "content": "Daqui pra frente responda em tabela.",
        }
    )
    snapshot = {
        "operationalFocus": {"productCode": "10080001"},
        "conversationState": {
            "activeTopic": "estoque",
            "activeTask": {
                "type": "stock_lookup",
                "label": "estoque",
                "objective": "consultar estoque",
                "status": "in_progress",
                "pending": ["ver fornecedores"],
            },
            "taskStack": [{"label": "playbook", "type": "playbook_creation", "status": "paused"}],
        },
    }
    summary = ChatConversationSummarizerService.build(
        previous_messages=previous,
        snapshot=snapshot,
    )

    assert summary.get("summary")
    assert any("10080001" in str(e) for e in summary.get("entities") or [])
    assert summary.get("decisions")
    assert summary.get("pending")
    assert summary.get("resumeHint")


def test_memory_pipeline_attaches_compressed_context():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="e os fornecedores?",
        previous_messages=_long_history(12),
    )

    assert snapshot.get("conversationSummary")
    assert snapshot.get("compressedContext")
    assert snapshot["compressedContext"].get("promptText")

    block = ChatConversationMemoryService.format_prompt_block(snapshot)

    assert "Resumo da conversa" in block
