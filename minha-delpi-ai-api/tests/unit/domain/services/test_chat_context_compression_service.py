"""Testes — ChatContextCompressionService (Fase 4)."""

from __future__ import annotations

from app.domain.services.chat_context_compression_service import (
    ChatContextCompressionService,
)
from app.domain.services.chat_conversation_summarizer_service import (
    ChatConversationSummarizerService,
)


def _messages(n: int):
    return [{"role": "user", "content": f"Mensagem {i}"} for i in range(n)]


def test_compress_respects_char_budget():
    previous = _messages(14)
    summary = ChatConversationSummarizerService.build(
        previous_messages=previous,
        snapshot={"conversationState": {"activeTopic": "testes"}},
    )
    compressed = ChatContextCompressionService.compress(
        summary,
        previous_messages=previous,
    )

    assert compressed["strategy"] in (
        ChatContextCompressionService.STRATEGY_STRUCTURED_PRIORITY,
        ChatContextCompressionService.STRATEGY_HIERARCHICAL,
    )
    assert len(compressed["promptText"]) <= ChatContextCompressionService.MAX_PROMPT_CHARS
    assert compressed["structured"]["summary"]


def test_apply_skips_short_sessions():
    snapshot = {"operationalFocus": {}}

    result = ChatContextCompressionService.apply_to_snapshot(
        snapshot,
        previous_messages=_messages(4),
    )

    assert "conversationSummary" not in result
    assert "compressedContext" not in result
