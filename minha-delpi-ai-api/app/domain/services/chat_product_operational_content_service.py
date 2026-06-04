"""Textos operacionais de produto — escopos, apresentação, plural."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
    invalidate_assistant_content_cache,
)

_BUNDLE = "product_operational_content"


def invalidate_product_operational_content_cache() -> None:
    invalidate_assistant_content_cache(_BUNDLE)


class ChatProductOperationalContentService:
    @classmethod
    def get(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def format(cls, *path: str, default: str = "", **values) -> str:
        return ChatAssistantContentService.format(_BUNDLE, *path, default=default, **values)

    @classmethod
    def list(cls, *path: str) -> list[str]:
        return ChatAssistantContentService.list(_BUNDLE, *path)

    @classmethod
    def get_mapping(cls, *path: str) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(_BUNDLE, *path)

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
        stems_node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "pluralPhrasing",
            "linkedScopeStems",
        )
        stems = stems_node.get(scope) if isinstance(stems_node, dict) else None

        if not isinstance(stems, list):
            return ()

        return tuple(str(item) for item in stems if str(item).strip())

    @classmethod
    def scope_term_groups(cls, scope: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        entry = ChatAssistantContentService.get_node(_BUNDLE, "pluralPhrasing", "scopeTerms", scope)

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
