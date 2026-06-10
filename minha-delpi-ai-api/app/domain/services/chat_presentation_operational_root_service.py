"""Desembrulha envelopes operacionais `{ wrapper: { items } }` — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationOperationalRootService:
    """Localiza sub-raiz com lista ``items`` para builders de perfil."""

    @classmethod
    def resolve_items_root(
        cls,
        root: dict | None,
        *,
        path: str = "",
        entity: str | None = None,
    ) -> dict | None:
        if not isinstance(root, dict):
            return None

        items_key, wrapper_keys = cls._config(path=path, entity=entity)

        items = root.get(items_key)

        if isinstance(items, list) and items:
            return root

        for wrapper in wrapper_keys:
            nested = root.get(wrapper)

            if not isinstance(nested, dict):
                continue

            nested_items = nested.get(items_key)

            if isinstance(nested_items, list) and nested_items:
                return nested

        return None

    @classmethod
    def resolve_bundle_root(
        cls,
        root: dict | None,
        *,
        path: str = "",
        entity: str | None = None,
    ) -> dict | None:
        if not isinstance(root, dict):
            return None

        items_root = cls.resolve_items_root(root, path=path, entity=entity)

        return items_root if items_root is not None else root

    @classmethod
    def _config(cls, *, path: str, entity: str | None) -> tuple[str, tuple[str, ...]]:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        raw = profile.get("operationalRoot")

        if isinstance(raw, dict):
            items_key = str(raw.get("itemsKey") or "items").strip() or "items"
            wrappers = raw.get("wrapperKeys") or raw.get("wrappers") or []

            if isinstance(wrappers, list) and wrappers:
                return items_key, tuple(str(key).strip() for key in wrappers if str(key).strip())

        items_key = ChatPresentationVocabularyService.hierarchy_tree_text(
            "operationalRootItemsKey",
            default="items",
        )
        wrapper_keys = ChatPresentationVocabularyService.hierarchy_tree_terms(
            "operationalRootWrapperKeys",
        )

        return items_key or "items", wrapper_keys or ("stock",)
