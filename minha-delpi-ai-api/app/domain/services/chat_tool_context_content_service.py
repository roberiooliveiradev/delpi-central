"""Textos do pipeline de tool context — bundle tool_context.json."""

from __future__ import annotations

import re

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_COMPILED_LISTS: dict[str, tuple[re.Pattern[str], ...]] = {}


class ChatToolContextContentService:
    _BUNDLE = "tool_context"

    @classmethod
    def list(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(cls._BUNDLE, *path))

    @classmethod
    def get(cls, *path: str) -> str:
        return ChatAssistantContentService.get(cls._BUNDLE, *path)

    @classmethod
    def format(cls, *path: str, **values: str) -> str:
        return ChatAssistantContentService.format(cls._BUNDLE, *path, **values)

    @classmethod
    def get_node(cls, *path: str):
        return ChatAssistantContentService.get_node(cls._BUNDLE, *path)

    @classmethod
    def compile_pattern_list(cls, *path: str) -> tuple[re.Pattern[str], ...]:
        cache_key = ".".join(path)

        if cache_key not in _COMPILED_LISTS:
            _COMPILED_LISTS[cache_key] = tuple(
                re.compile(str(item), re.IGNORECASE)
                for item in cls.list(*path)
                if str(item).strip()
            )

        return _COMPILED_LISTS[cache_key]

    @classmethod
    def native_max_schemas_per_call(cls, *, default: int = 12) -> int:
        node = cls.get_node("nativeToolCalling")
        raw = node.get("maxSchemasPerCall") if isinstance(node, dict) else None

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return max(1, int(default))

    @classmethod
    def native_default_max_tool_calls(cls, *, default: int = 3) -> int:
        node = cls.get_node("nativeToolCalling")
        raw = node.get("defaultMaxToolCalls") if isinstance(node, dict) else None

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return max(1, int(default))
