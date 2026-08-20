"""Loader canônico de `intent_router.json` — frases, limites e padrões compilados."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "intent_router"
_COMPILED_LISTS: dict[str, tuple[re.Pattern[str], ...]] = {}


class ChatIntentRouterContentService:
    @classmethod
    def list(cls, *path: str) -> list[str]:
        return ChatAssistantContentService.list(_BUNDLE, *path)

    @classmethod
    def get_node(cls, *path: str) -> Any:
        return ChatAssistantContentService.get_node(_BUNDLE, *path)

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        node = cls.get_node("limits")
        if not isinstance(node, dict):
            return default
        raw = node.get(key, default)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def phrases(cls, key: str) -> tuple[str, ...]:
        return tuple(cls.list(key))

    @classmethod
    def short_context_reply_patterns(cls) -> tuple[re.Pattern[str], ...]:
        cache_key = "shortContextReplyPatterns"
        if cache_key not in _COMPILED_LISTS:
            compiled: list[re.Pattern[str]] = []
            for raw in cls.list(cache_key):
                text = str(raw or "").strip()
                if not text:
                    continue
                try:
                    compiled.append(re.compile(text, re.IGNORECASE))
                except re.error:
                    continue
            _COMPILED_LISTS[cache_key] = tuple(compiled)
        return _COMPILED_LISTS[cache_key]

    @classmethod
    def invalidate_cache(cls) -> None:
        _COMPILED_LISTS.clear()
