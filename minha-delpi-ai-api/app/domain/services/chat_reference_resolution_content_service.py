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
