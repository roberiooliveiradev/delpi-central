"""Detecção de perguntas sobre inventário e escopo de fontes de projeto."""

from __future__ import annotations

import re

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatProjectSourcesIntentService:
    _BUNDLE = "turn_preparation"
    _CONTENT_PREFIX = ("directAnswers", "projectSources")

    @classmethod
    def _normalized(cls, message: str) -> str:
        return re.sub(r"\s+", " ", str(message or "").strip().lower())

    @classmethod
    def _phrase_list(cls, key: str) -> tuple[str, ...]:
        phrases = ChatAssistantContentService.list(
            cls._BUNDLE,
            *cls._CONTENT_PREFIX,
            key,
        )

        return tuple(phrase.strip().lower() for phrase in phrases if phrase.strip())

    @classmethod
    def _matches_any(cls, message: str, key: str) -> bool:
        normalized = cls._normalized(message)

        if not normalized:
            return False

        return any(phrase in normalized for phrase in cls._phrase_list(key))

    @classmethod
    def is_inventory_question(cls, message: str) -> bool:
        return cls._matches_any(message, "inventoryPhrases")

    @classmethod
    def should_restrict_to_project_sources(cls, message: str) -> bool:
        if cls.is_inventory_question(message):
            return True

        return cls._matches_any(message, "scopedPhrases")
