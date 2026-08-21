"""Loader canônico — bundle ``email_intent.json``."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "email_intent"


class ChatEmailIntentContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def markers(cls) -> tuple[re.Pattern[str], ...]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "markers") or []

        return tuple(
            re.compile(str(item), re.IGNORECASE)
            for item in node
            if str(item or "").strip()
        )

    @classmethod
    @lru_cache(maxsize=1)
    def subtypes(cls) -> dict[str, tuple[re.Pattern[str], ...]]:
        return cls._pattern_groups("subtypes")

    @classmethod
    @lru_cache(maxsize=1)
    def tones(cls) -> dict[str, tuple[re.Pattern[str], ...]]:
        return cls._pattern_groups("tones")

    @classmethod
    @lru_cache(maxsize=1)
    def audiences(cls) -> dict[str, tuple[re.Pattern[str], ...]]:
        return cls._pattern_groups("audiences")

    @classmethod
    @lru_cache(maxsize=4)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")

        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")

        flags = re.IGNORECASE

        if key == "signatureExplicit":
            flags |= re.MULTILINE
        elif key == "subjectFromAnswer":
            flags = re.IGNORECASE | re.MULTILINE

        return re.compile(str(source), flags)

    @classmethod
    def _pattern_groups(cls, section: str) -> dict[str, tuple[re.Pattern[str], ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, section)

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
        cls.markers.cache_clear()
        cls.subtypes.cache_clear()
        cls.tones.cache_clear()
        cls.audiences.cache_clear()
        cls.compile_pattern.cache_clear()
