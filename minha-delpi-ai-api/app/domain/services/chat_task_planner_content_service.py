"""Loader canônico de configuração do TaskPlanner (E5)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "conversational_intelligence"
_SECTION = "taskPlanner"


class ChatTaskPlannerContentService:
    BUNDLE = _BUNDLE

    @classmethod
    def _section(cls, key: str) -> Any:
        node = ChatAssistantContentService.get_node(_BUNDLE, _SECTION)

        if not isinstance(node, dict):
            return None

        return node.get(key)

    @classmethod
    def mode_limit_int(cls, key: str, mode: str, default: int) -> int:
        node = cls._section(key)

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(str(mode or "").strip().lower(), default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def default_int(cls, key: str, default: int) -> int:
        node = cls._section("defaults")

        if not isinstance(node, dict):
            return default

        try:
            return int(node.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def default_text(cls, key: str, default: str = "") -> str:
        node = cls._section("defaults")

        if not isinstance(node, dict):
            return default

        value = node.get(key, default)

        return str(value or default).strip() or default

    @classmethod
    def string_list(cls, key: str) -> tuple[str, ...]:
        node = cls._section(key)

        if not isinstance(node, list):
            return ()

        return tuple(
            str(item or "").strip().lower() for item in node if str(item or "").strip()
        )

    @classmethod
    def string_map(cls, key: str) -> dict[str, str]:
        node = cls._section(key)

        if not isinstance(node, dict):
            return {}

        return {
            str(raw_key): str(raw_value or "").strip()
            for raw_key, raw_value in node.items()
            if str(raw_value or "").strip()
        }
