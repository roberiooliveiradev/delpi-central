"""Loader canônico — bundle ``user_context_items.json``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "user_context_items"


class ChatUserContextItemsContentService:
    @classmethod
    @lru_cache(maxsize=8)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")

        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")

        flags = re.IGNORECASE

        if key in {"tableRow", "sectionEnd"}:
            flags |= re.MULTILINE

        return re.compile(str(source), flags)

    @classmethod
    def prompt_marker(cls) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "promptMarker",
            default="Contexto adicionado pelo usuário",
        )

    @classmethod
    def limit_int(cls, key: str, *, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits", key)

        try:
            value = int(node)
        except (TypeError, ValueError):
            return default

        return value if value > 0 else default

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
