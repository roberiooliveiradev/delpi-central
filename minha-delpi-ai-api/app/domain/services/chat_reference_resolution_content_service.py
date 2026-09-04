"""Loader canônico — padrões de referência vaga (`reference_resolution.json`)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatReferenceResolutionContentService:
    BUNDLE = "reference_resolution"

    @classmethod
    @lru_cache(maxsize=32)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(
            cls.BUNDLE,
            "patterns",
            key,
            default="",
        )
        if not source.strip():
            raise KeyError(f"{cls.BUNDLE}.patterns.{key} ausente")
        return re.compile(source, re.IGNORECASE)

    @classmethod
    def coreference_text(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            cls.BUNDLE,
            "coreference",
            key,
            default=default,
        )

    @classmethod
    def coreference_confidence(cls, key: str, *, default: float = 0.7) -> float:
        node = ChatAssistantContentService.get_node(cls.BUNDLE, "coreference")

        if not isinstance(node, dict):
            return default

        try:
            return float(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def ambiguity_text(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            cls.BUNDLE,
            "ambiguity",
            key,
            default=default,
        )

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
