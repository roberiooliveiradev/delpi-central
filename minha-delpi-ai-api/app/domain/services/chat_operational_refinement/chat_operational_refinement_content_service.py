"""Loader canônico — bundle ``operational_refinement.json``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "operational_refinement"


class ChatOperationalRefinementContentService:
    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")

        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")

        return re.compile(str(source), re.IGNORECASE)

    @classmethod
    @lru_cache(maxsize=4)
    def compile_pattern_list(cls, key: str) -> tuple[re.Pattern[str], ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "patterns", key)

        if not isinstance(node, list) or not node:
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente ou vazio")

        compiled: list[re.Pattern[str]] = []

        for item in node:
            source = str(item or "").strip()

            if not source:
                continue

            compiled.append(re.compile(source, re.IGNORECASE))

        if not compiled:
            raise KeyError(f"{_BUNDLE}.patterns.{key} sem padrões válidos")

        return tuple(compiled)

    @classmethod
    @lru_cache(maxsize=16)
    def terms(cls, key: str) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "terms", key)

        if not isinstance(node, list):
            return ()

        return tuple(str(item) for item in node if str(item or "").strip())

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
        cls.compile_pattern_list.cache_clear()
        cls.terms.cache_clear()
