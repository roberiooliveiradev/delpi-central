"""Catálogo JSON `learning_content` — textos, padrões e limites de aprendizagem."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "learning_content"
_COMPILED: dict[str, re.Pattern[str]] = {}
_COMPILED_LISTS: dict[str, tuple[re.Pattern[str], ...]] = {}


class ChatLearningContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            *path,
            default=default,
            **values,
        )

    @classmethod
    def list(cls, *path: str) -> list[Any]:
        return ChatAssistantContentService.list(_BUNDLE, *path)

    @classmethod
    def get_node(cls, *path: str) -> Any:
        return ChatAssistantContentService.get_node(_BUNDLE, *path)

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        raw = cls.get("limits", key, default=str(default))

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def limit_float(cls, key: str, default: float) -> float:
        raw = cls.get("limits", key, default=str(default))

        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def setting_float(cls, key: str, default: float) -> float:
        raw = cls.get("settings", key, default=str(default))

        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def setting_str(cls, key: str, default: str = "") -> str:
        return cls.get("settings", key, default=default)

    @classmethod
    def classification_kind(cls, key: str, default: str = "term") -> str:
        return cls.get("classification", key, default=default)

    @classmethod
    def safety_reason(cls, key: str) -> str:
        return cls.get("safetyReasons", key, default=key)

    @classmethod
    def risk_level(cls, key: str) -> str:
        return cls.get("riskLevels", key, default=key)

    @classmethod
    def ack_kind_key(cls, kind: str) -> str:
        node = cls.get_node("settings", "ackKindKeys") or {}

        return str(node.get(kind) or node.get("confirmed") or "confirmed")

    @classmethod
    def quote_chars(cls) -> str:
        items = cls.list("patternLists", "quoteChars")

        return "".join(str(item) for item in items)

    @classmethod
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        cache_key = f"pattern:{key}"

        if cache_key not in _COMPILED:
            raw = cls.get("patterns", key, default="")
            _COMPILED[cache_key] = re.compile(str(raw), re.IGNORECASE)

        return _COMPILED[cache_key]

    @classmethod
    def compile_pattern_list(cls, key: str) -> tuple[re.Pattern[str], ...]:
        cache_key = f"list:{key}"

        if cache_key not in _COMPILED_LISTS:
            patterns = cls.list("patternLists", key)
            _COMPILED_LISTS[cache_key] = tuple(
                re.compile(str(item), re.IGNORECASE)
                for item in patterns
                if str(item).strip()
            )

        return _COMPILED_LISTS[cache_key]

    @classmethod
    def compile_term_meaning_pattern(cls, term: str) -> re.Pattern[str]:
        template = cls.get("patterns", "explicitMeaningForTerm", default="")
        pattern = str(template).replace("{term}", re.escape(str(term or "").strip()))

        return re.compile(pattern, re.IGNORECASE)

    @classmethod
    def explicit_definition_patterns(cls) -> tuple[re.Pattern[str], ...]:
        order = cls.list("patternLists", "explicitDefinitionOrder")
        patterns: list[re.Pattern[str]] = []

        for key in order:
            key_name = str(key).strip()

            if key_name:
                patterns.append(cls.compile_pattern(key_name))

        return tuple(patterns)
