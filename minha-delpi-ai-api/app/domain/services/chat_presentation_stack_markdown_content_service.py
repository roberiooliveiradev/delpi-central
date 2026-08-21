"""Loader canônico — marcadores e regex do stack markdown (`presenter_content`)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatPresentationStackMarkdownContentService:
    @classmethod
    def highlights_header(cls) -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "stackMarkdownMarkers",
            "highlightsHeader",
            default="**Destaques**",
        )

    @classmethod
    def attention_header_prefix(cls) -> str:
        return ChatAssistantContentService.get(
            "presenter_content",
            "stackMarkdownMarkers",
            "attentionHeaderPrefix",
            default="**Pontos de atenção",
        )

    @classmethod
    @lru_cache(maxsize=8)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(
            "presenter_content",
            "stackMarkdownMarkers",
            "patterns",
            key,
            default="",
        )
        if not source.strip():
            raise KeyError(f"stackMarkdownMarkers.patterns.{key} ausente")
        return re.compile(source)

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
