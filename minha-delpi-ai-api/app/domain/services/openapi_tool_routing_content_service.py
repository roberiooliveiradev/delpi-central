"""Loader canônico de openapi_tool_routing.json."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def invalidate_openapi_tool_routing_cache() -> None:
    _bundle.cache_clear()


@lru_cache(maxsize=1)
def _bundle() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("openapi_tool_routing")


class OpenApiToolRoutingContentService:
    @classmethod
    def get_node(cls, *path: str) -> Any:
        node: Any = _bundle()
        for key in path:
            if not isinstance(node, dict):
                return None
            node = node.get(key)
        return node

    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        node = cls.get_node(*path)
        if node is None:
            return default
        if isinstance(node, str):
            return node
        return default

    @classmethod
    def int_setting(cls, *path: str, default: int = 0) -> int:
        node = cls.get_node(*path)
        try:
            return int(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def float_setting(cls, *path: str, default: float = 0.0) -> float:
        node = cls.get_node(*path)
        try:
            return float(node)
        except (TypeError, ValueError):
            return default

    @classmethod
    def list_setting(cls, *path: str) -> list[str]:
        node = cls.get_node(*path)
        if not isinstance(node, list):
            return []
        return [str(item) for item in node if str(item).strip()]
