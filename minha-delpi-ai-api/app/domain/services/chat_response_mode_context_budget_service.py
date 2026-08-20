"""Orçamento de contexto conversacional por modo (Rápida / Normal / Pensador)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


@dataclass(frozen=True)
class ChatContextBudget:
    mode: str
    history_max_messages: int
    history_summary_max_chars: int
    rag_max_chunks: int
    rag_max_chars: int
    tool_context_max_chars: int
    message_search_max_hits: int
    message_search_max_chars: int
    message_search_lookback_messages: int
    max_multi_actions_per_turn: int

    def as_admin_debug(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "historyMaxMessages": self.history_max_messages,
            "historySummaryMaxChars": self.history_summary_max_chars,
            "ragMaxChunks": self.rag_max_chunks,
            "ragMaxChars": self.rag_max_chars,
            "toolContextMaxChars": self.tool_context_max_chars,
            "messageSearchMaxHits": self.message_search_max_hits,
            "messageSearchMaxChars": self.message_search_max_chars,
            "messageSearchLookbackMessages": self.message_search_lookback_messages,
            "maxMultiActionsPerTurn": self.max_multi_actions_per_turn,
        }

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChatResponseModeContextBudgetService:
    """Fonte única: history / RAG / tool clip / message search por responseMode."""

    _DEFAULTS: dict[str, dict[str, int]] = {
        "fast": {
            "historyMaxMessages": 4,
            "historySummaryMaxChars": 600,
            "ragMaxChunks": 3,
            "ragMaxChars": 4000,
            "toolContextMaxChars": 4000,
            "messageSearchMaxHits": 3,
            "messageSearchMaxChars": 1500,
            "messageSearchLookbackMessages": 40,
            "maxMultiActionsPerTurn": 1,
        },
        "normal": {
            "historyMaxMessages": 12,
            "historySummaryMaxChars": 1500,
            "ragMaxChunks": 6,
            "ragMaxChars": 9000,
            "toolContextMaxChars": 9000,
            "messageSearchMaxHits": 6,
            "messageSearchMaxChars": 3500,
            "messageSearchLookbackMessages": 80,
            "maxMultiActionsPerTurn": 4,
        },
        "thinker": {
            "historyMaxMessages": 20,
            "historySummaryMaxChars": 2500,
            "ragMaxChunks": 8,
            "ragMaxChars": 12000,
            "toolContextMaxChars": 12000,
            "messageSearchMaxHits": 10,
            "messageSearchMaxChars": 6000,
            "messageSearchLookbackMessages": 120,
            "maxMultiActionsPerTurn": 6,
        },
    }

    @classmethod
    def resolve(cls, response_mode: str | None) -> ChatContextBudget:
        mode = ChatResponseModeService.normalize(response_mode)
        defaults = cls._DEFAULTS.get(mode) or cls._DEFAULTS["normal"]
        node = ChatResponseModeContentService.context_budget_node(mode)

        def _int(key: str, *, minimum: int = 1) -> int:
            raw = node.get(key) if isinstance(node, dict) else None
            if raw in (None, ""):
                raw = defaults.get(key)
            try:
                return max(minimum, int(raw))
            except (TypeError, ValueError):
                return max(minimum, int(defaults.get(key) or minimum))

        return ChatContextBudget(
            mode=mode,
            history_max_messages=_int("historyMaxMessages"),
            history_summary_max_chars=_int("historySummaryMaxChars", minimum=100),
            rag_max_chunks=_int("ragMaxChunks"),
            rag_max_chars=_int("ragMaxChars", minimum=500),
            tool_context_max_chars=_int("toolContextMaxChars", minimum=500),
            message_search_max_hits=_int("messageSearchMaxHits"),
            message_search_max_chars=_int("messageSearchMaxChars", minimum=200),
            message_search_lookback_messages=_int(
                "messageSearchLookbackMessages",
                minimum=10,
            ),
            max_multi_actions_per_turn=_int("maxMultiActionsPerTurn"),
        )

    @classmethod
    def history_keep(cls, response_mode: str | None) -> int:
        return cls.resolve(response_mode).history_max_messages

    @classmethod
    def max_multi_actions_per_turn(cls, response_mode: str | None) -> int:
        return cls.resolve(response_mode).max_multi_actions_per_turn
