"""Loader genérico de JSON em app/content/pt-BR/assistant/*."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


def invalidate_assistant_content_cache(bundle: str | None = None) -> None:
    if bundle is None:
        _bundle_content.cache_clear()
        return

    _bundle_content.cache_clear()


@lru_cache(maxsize=32)
def _bundle_content(bundle: str) -> dict[str, Any]:
    normalized = str(bundle or "").strip().removesuffix(".json")

    return ContentService.load_json(f"assistant/{normalized}")


class ChatAssistantContentService:
    @classmethod
    def get(cls, bundle: str, *path: str, default: str = "") -> str:
        node: Any = _bundle_content(bundle)

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
    def format(cls, bundle: str, *path: str, default: str = "", **values) -> str:
        template = cls.get(bundle, *path, default=default)

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template

    @classmethod
    def list(cls, bundle: str, *path: str) -> list[str]:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return []

            node = node.get(key)

        if not isinstance(node, list):
            return []

        return [str(item) for item in node if str(item).strip()]

    @classmethod
    def get_mapping(cls, bundle: str, *path: str) -> dict[str, str]:
        node: Any = _bundle_content(bundle)

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
    def get_error_type(cls, error_type: str, field: str, *, default: str = "") -> str:
        node: Any = _bundle_content("error_handling").get("types", {}).get(error_type, {})

        if not isinstance(node, dict):
            return default

        value = node.get(field)

        if value is None:
            return default

        if isinstance(value, str):
            return value

        return default

    @classmethod
    def get_error_reasons(cls, error_type: str) -> list[str]:
        node: Any = _bundle_content("error_handling").get("types", {}).get(error_type, {})

        if not isinstance(node, dict):
            return []

        reasons = node.get("reasons")

        if not isinstance(reasons, list):
            return []

        return [str(item) for item in reasons if str(item).strip()]

    @classmethod
    def get_node(cls, bundle: str, *path: str) -> Any:
        node: Any = _bundle_content(bundle)

        for key in path:
            if not isinstance(node, dict):
                return None

            node = node.get(key)

        return node

    @classmethod
    def title_for_path(
        cls,
        bundle: str,
        path: str,
        *,
        path_key: str = "titlesByPathFragment",
        default: str | None = None,
    ) -> str | None:
        """Primeiro fragmento de path que casar no mapa de títulos (ordem do JSON)."""
        lowered = str(path or "").lower()
        fragments = cls.get_mapping(bundle, path_key)

        for fragment, label in fragments.items():
            if fragment in lowered:
                return label

        return default
