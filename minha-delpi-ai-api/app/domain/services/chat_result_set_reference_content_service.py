"""Loader canônico do bundle ``result_set_references`` (E2.S2)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "result_set_references"


class ChatResultSetReferenceContentService:
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
    def limit_float(cls, key: str, default: float) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, "limits")

        if not isinstance(node, dict):
            return default

        try:
            return float(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def field_names(cls, group: str) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "fields", group)
            if str(item).strip()
        )

    @classmethod
    def kind(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "kinds", key, default=key) or key
        ).strip()

    @classmethod
    def ordinal_words(cls) -> dict[str, int]:
        return cls._int_mapping("ordinals", "words")

    @classmethod
    def cardinal_words(cls) -> dict[str, int]:
        return cls._int_mapping("ordinals", "cardinals")

    @classmethod
    def ordinal_label(cls, ordinal: int) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "ordinalWords",
                str(int(ordinal)),
                default=str(int(ordinal)),
            )
            or str(int(ordinal))
        ).strip()

    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(
            _BUNDLE,
            "ordinals",
            "patterns",
            key,
            default="",
        )

        if not source.strip():
            raise KeyError(f"{_BUNDLE}.ordinals.patterns.{key} ausente")

        return re.compile(source, re.IGNORECASE)

    @classmethod
    def resolution_text(cls, key: str, **values) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "resolution",
            key,
            default="",
            **values,
        )

    @classmethod
    def resolution_value(cls, key: str, *, default: str = "") -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "resolution", key, default=default)
            or default
        ).strip()

    @classmethod
    def resolution_confidence(cls) -> float:
        node = ChatAssistantContentService.get_node(_BUNDLE, "resolution")

        if not isinstance(node, dict):
            return 0.85

        try:
            return float(node.get("confidence", 0.85))
        except (TypeError, ValueError):
            return 0.85

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.compile_pattern.cache_clear()

    @classmethod
    def _int_mapping(cls, *path: str) -> dict[str, int]:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        if not isinstance(node, dict):
            return {}

        resolved: dict[str, int] = {}

        for key, value in node.items():
            token = str(key).strip().lower()

            if not token:
                continue

            try:
                resolved[token] = int(value)
            except (TypeError, ValueError):
                continue

        return resolved
