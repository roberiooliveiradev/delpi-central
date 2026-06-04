"""Textos operacionais de produto — escopos, apresentação, plural e web search."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


def invalidate_product_operational_content_cache() -> None:
    _content.cache_clear()


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/product_operational_content")


class ChatProductOperationalContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        node: Any = _content()

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
    def list(cls, *path: str) -> list[str]:
        node: Any = _content()

        for key in path:
            if not isinstance(node, dict):
                return []

            node = node.get(key)

        if not isinstance(node, list):
            return []

        return [str(item) for item in node if str(item).strip()]

    @classmethod
    def get_mapping(cls, *path: str) -> dict[str, str]:
        node: Any = _content()

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
    def scope_label_for_scope_key(cls, scope_key: str, *, default: str | None = None) -> str:
        labels = cls.get_mapping("scopes", "byScopeKey")
        fallback = default if default is not None else scope_key

        return labels.get(scope_key, fallback)

    @classmethod
    def scope_labels_from_api_path(cls, path: str) -> list[str]:
        lowered = str(path or "").lower()
        labels: list[str] = []
        fragments = cls.get_mapping("scopes", "byPathFragment")

        for fragment, label in fragments.items():
            if fragment in lowered and label not in labels:
                labels.append(label)

        return labels

    @classmethod
    def composite_short_scope_labels_from_path(cls, path: str) -> list[str]:
        lowered = str(path or "").lower()
        labels: list[str] = []
        fragments = cls.get_mapping("scopes", "compositeShort")

        for fragment, label in fragments.items():
            if fragment in lowered and label not in labels:
                labels.append(label)

        return labels

    @classmethod
    def join_list_pt(cls, items: list[str]) -> str:
        if not items:
            return ""

        if len(items) == 1:
            return items[0]

        if len(items) == 2:
            return cls.format("listJoin", "two", first=items[0], second=items[1])

        return cls.format("listJoin", "many", head=", ".join(items[:-1]), last=items[-1])

    @classmethod
    def linked_scope_stems(cls, scope: str) -> tuple[str, ...]:
        node: Any = _content().get("pluralPhrasing", {}).get("linkedScopeStems", {})

        if not isinstance(node, dict):
            return ()

        stems = node.get(scope)

        if not isinstance(stems, list):
            return ()

        return tuple(str(item) for item in stems if str(item).strip())

    @classmethod
    def scope_term_groups(cls, scope: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        node: Any = _content().get("pluralPhrasing", {}).get("scopeTerms", {})

        if not isinstance(node, dict):
            return (), ()

        entry = node.get(scope)

        if not isinstance(entry, dict):
            return (), ()

        terms = entry.get("terms")
        plural_terms = entry.get("pluralTerms")

        return (
            tuple(str(item) for item in terms if isinstance(terms, list) and str(item).strip()),
            tuple(
                str(item)
                for item in plural_terms
                if isinstance(plural_terms, list) and str(item).strip()
            ),
        )
