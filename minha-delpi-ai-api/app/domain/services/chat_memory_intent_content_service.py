"""Loader canônico — bundle ``memory_intent.json``."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "memory_intent"


class ChatMemoryIntentContentService:
    @classmethod
    @lru_cache(maxsize=32)
    def compile_pattern(cls, *path: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, *path, default="")

        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.{'.'.join(path)} ausente")

        flags = re.IGNORECASE

        if path == ("sessionClear", "pattern"):
            flags |= re.DOTALL

        return re.compile(str(source), flags)

    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern_list(cls, *path: str) -> tuple[re.Pattern[str], ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if not isinstance(node, list) or not node:
            raise KeyError(f"{_BUNDLE}.{'.'.join(path)} ausente ou vazio")

        compiled: list[re.Pattern[str]] = []

        for item in node:
            source = str(item or "").strip()

            if source:
                compiled.append(re.compile(source, re.IGNORECASE))

        if not compiled:
            raise KeyError(f"{_BUNDLE}.{'.'.join(path)} sem padrões válidos")

        return tuple(compiled)

    @classmethod
    def limit_int(cls, *path: str, default: int = 0) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        try:
            value = int(node)
        except (TypeError, ValueError):
            return default

        return value

    @classmethod
    def limit_float(cls, *path: str, default: float = 0.0) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        try:
            return float(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def string_list(cls, *path: str) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if not isinstance(node, list):
            return ()

        return tuple(str(item) for item in node if str(item or "").strip())

    @classmethod
    def string_map(cls, *path: str) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if not isinstance(node, dict):
            return {}

        return {
            str(key): str(value)
            for key, value in node.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def pattern_map(cls, *path: str) -> dict[str, tuple[re.Pattern[str], ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if not isinstance(node, dict):
            return {}

        resolved: dict[str, tuple[re.Pattern[str], ...]] = {}

        for key, raw in node.items():
            if not isinstance(raw, list):
                continue

            compiled = tuple(
                re.compile(str(item), re.IGNORECASE)
                for item in raw
                if str(item or "").strip()
            )

            if compiled:
                resolved[str(key)] = compiled

        return resolved

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()
        cls.compile_pattern_list.cache_clear()
