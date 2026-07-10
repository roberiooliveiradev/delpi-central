"""Loader canônico de `drawing_query_intent.json`."""

from __future__ import annotations

import unicodedata
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "drawing_query_intent"


class ChatDrawingQueryIntentContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *path,
            default=default,
            **values,
        )

    @classmethod
    def list_values(cls, *path: str) -> list[str]:
        raw = ChatAssistantContentService.list(_BUNDLE, *path)
        return [str(item) for item in raw if str(item).strip()]

    @classmethod
    def get_node(cls, *path: str) -> Any:
        return ChatAssistantContentService.get_node(_BUNDLE, *path)

    @classmethod
    def normalize_message(cls, message: str | None) -> str:
        folded = str(message or "").casefold()
        decomposed = unicodedata.normalize("NFD", folded)
        return "".join(
            char for char in decomposed if unicodedata.category(char) != "Mn"
        )

    @classmethod
    def matches_trigger_category(cls, normalized_message: str, category: str) -> bool:
        phrases = cls.list_values("reportAdjustmentTriggers", category)
        return any(
            cls.normalize_message(phrase) in normalized_message
            for phrase in phrases
            if str(phrase).strip()
        )
