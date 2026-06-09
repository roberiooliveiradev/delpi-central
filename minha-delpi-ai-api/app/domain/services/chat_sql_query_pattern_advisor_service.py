"""Padrões SQL avançados (CTE, window) — Playbook §25–31."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)


class ChatSqlQueryPatternAdvisorService:
    @classmethod
    def _patterns(cls) -> tuple[tuple[tuple[str, ...], str, str], ...]:
        return ChatSqlIntentVocabularyService.query_advisor_patterns()

    @classmethod
    def recommend(cls, message: str | None) -> dict[str, Any]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        patterns: list[dict[str, str]] = []
        hints: list[str] = []

        if not normalized:
            return {"patterns": patterns, "hints": hints}

        for triggers, code, guidance in cls._patterns():
            if any(trigger in normalized for trigger in triggers):
                patterns.append({"code": code, "guidance": guidance})
                hints.append(code)

        return {"patterns": patterns, "hints": hints}
