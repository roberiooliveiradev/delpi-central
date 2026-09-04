"""Loader canônico do bundle ``turn_understanding`` (E3.S1)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "turn_understanding"


class ChatTurnUnderstandingContentService:
    BUNDLE = _BUNDLE

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits")

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")

        if not source.strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")

        return re.compile(source, re.IGNORECASE)

    @classmethod
    def verbs(cls, group: str) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "verbs", group)
            if str(item).strip()
        )

    @classmethod
    def kind(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "kinds", key, default=key) or key
        ).strip()

    @classmethod
    def dependency_markers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "dependencyMarkers")
            if str(item).strip()
        )

    @classmethod
    def confidence(cls, key: str, default: float) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, "confidence")

        if not isinstance(node, dict):
            return default

        try:
            return float(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def continuation_max_hint_chars(cls) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "continuation")

        if not isinstance(node, dict):
            return 120

        try:
            return max(16, int(node.get("maxHintChars", 120)))
        except (TypeError, ValueError):
            return 120

    @classmethod
    def noise_tokens(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "noiseTokens")
            if str(item).strip()
        )

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
