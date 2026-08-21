"""Loader canônico — bundle ``text_quality.json``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "text_quality"


class ChatTextQualityContentService:
    @classmethod
    @lru_cache(maxsize=8)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")

        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")

        return re.compile(str(source), re.IGNORECASE)

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
