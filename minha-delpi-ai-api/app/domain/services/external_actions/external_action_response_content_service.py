"""Textos de resposta de actions externas — carregados de app/content/pt-BR/."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


def invalidate_external_action_response_cache() -> None:
    _responses_content.cache_clear()


@lru_cache(maxsize=1)
def _responses_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/external_action_responses")


class ExternalActionResponseContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        node: Any = _responses_content()

        for key in path:
            if not isinstance(node, dict):
                return default

            node = node.get(key)

        if node is None:
            return default

        if isinstance(node, str):
            return node

        return default

    @classmethod
    def format(cls, *path: str, default: str = "", **values) -> str:
        template = cls.get(*path, default=default)

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template

    @classmethod
    def get_mapping(cls, *path: str) -> dict[str, str]:
        node: Any = _responses_content()

        for key in path:
            if not isinstance(node, dict):
                return {}

            node = node.get(key)

        if not isinstance(node, dict):
            return {}

        return {
            str(item_key): str(item_value)
            for item_key, item_value in node.items()
            if str(item_key).strip() and item_value is not None
        }

    @classmethod
    def list(cls, *path: str) -> list[str]:
        node: Any = _responses_content()

        for key in path:
            if not isinstance(node, dict):
                return []

            node = node.get(key)

        if not isinstance(node, list):
            return []

        return [str(item) for item in node if str(item).strip()]

    @classmethod
    def weekday_label(cls, weekday: int) -> str:
        labels = cls.list("temporal", "weekdays")
        if 0 <= weekday < len(labels):
            return labels[weekday]
        return ""
