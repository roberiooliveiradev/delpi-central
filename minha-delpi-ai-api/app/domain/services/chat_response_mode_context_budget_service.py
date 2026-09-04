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
    profile: str
    history_max_messages: int
    history_summary_max_chars: int
    rag_max_chunks: int
    rag_max_chars: int
    tool_context_max_chars: int
    message_search_max_hits: int
    message_search_max_chars: int
    message_search_lookback_messages: int
    max_multi_actions_per_turn: int
    prior_turn_facts_pre_tool_max_chars: int
    prior_turn_facts_synthesis_max_chars: int

    def as_admin_debug(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "profile": self.profile,
            "historyMaxMessages": self.history_max_messages,
            "historySummaryMaxChars": self.history_summary_max_chars,
            "ragMaxChunks": self.rag_max_chunks,
            "ragMaxChars": self.rag_max_chars,
            "toolContextMaxChars": self.tool_context_max_chars,
            "messageSearchMaxHits": self.message_search_max_hits,
            "messageSearchMaxChars": self.message_search_max_chars,
            "messageSearchLookbackMessages": self.message_search_lookback_messages,
            "maxMultiActionsPerTurn": self.max_multi_actions_per_turn,
            "priorTurnFactsPreToolMaxChars": self.prior_turn_facts_pre_tool_max_chars,
            "priorTurnFactsSynthesisMaxChars": self.prior_turn_facts_synthesis_max_chars,
        }

    def prior_turn_facts_max_chars(self, stage: str = "synthesis") -> int:
        token = str(stage or "synthesis").strip().lower()
        if token in {"pre_tool", "pretool", "pre-tool"}:
            return self.prior_turn_facts_pre_tool_max_chars
        return self.prior_turn_facts_synthesis_max_chars

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
            "priorTurnFactsPreToolMaxChars": 400,
            "priorTurnFactsSynthesisMaxChars": 800,
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
            "priorTurnFactsPreToolMaxChars": 900,
            "priorTurnFactsSynthesisMaxChars": 1800,
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
            "priorTurnFactsPreToolMaxChars": 1400,
            "priorTurnFactsSynthesisMaxChars": 2800,
        },
    }

    @classmethod
    def resolve(cls, response_mode: str | None, *, provider: str | None = None) -> ChatContextBudget:
        mode = ChatResponseModeService.normalize(response_mode)
        profile = ChatResponseModeContentService.context_budget_profile_for_provider(provider)
        defaults = cls._DEFAULTS.get(mode) or cls._DEFAULTS["normal"]
        node = ChatResponseModeContentService.context_budget_node(mode, profile=profile)

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
            profile=profile,
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
            prior_turn_facts_pre_tool_max_chars=_int(
                "priorTurnFactsPreToolMaxChars",
                minimum=100,
            ),
            prior_turn_facts_synthesis_max_chars=_int(
                "priorTurnFactsSynthesisMaxChars",
                minimum=100,
            ),
        )

    @classmethod
    def current_profile(cls) -> str:
        provider = None

        try:
            from app.infrastructure.llm.llm_request_context import get_active_config

            provider = get_active_config().provider
        except Exception:
            provider = None

        if not provider:
            try:
                from app.infrastructure.config.llm_text_config import resolve_llm_text_config

                provider = resolve_llm_text_config().provider
            except Exception:
                provider = "ollama"

        return ChatResponseModeContentService.context_budget_profile_for_provider(provider)

    @classmethod
    def history_keep(cls, response_mode: str | None) -> int:
        return cls.resolve(response_mode).history_max_messages

    @classmethod
    def max_multi_actions_per_turn(cls, response_mode: str | None) -> int:
        return cls.resolve(response_mode).max_multi_actions_per_turn

    @classmethod
    def prior_turn_facts_max_chars(
        cls,
        response_mode: str | None,
        *,
        stage: str = "synthesis",
        provider: str | None = None,
    ) -> int:
        return cls.resolve(response_mode, provider=provider).prior_turn_facts_max_chars(
            stage
        )
