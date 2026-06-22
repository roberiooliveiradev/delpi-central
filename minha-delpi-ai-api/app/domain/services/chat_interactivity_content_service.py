"""Loader canônico — bundle `assistant/interactivity.json`."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


class ChatInteractivityContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        node = ContentService.load_json("assistant/interactivity")

        return node if isinstance(node, dict) else {}

    @classmethod
    def settings_bool(cls, key: str, *, default: bool = False) -> bool:
        settings = cls.bundle().get("settings")

        if not isinstance(settings, dict):
            return default

        value = settings.get(key)

        return bool(value) if value is not None else default

    @classmethod
    def hide_unavailable_suggestions(cls) -> bool:
        return cls.settings_bool("hideUnavailableSuggestions", default=True)

    @classmethod
    def max_primary(cls) -> int:
        raw = cls.bundle().get("maxPrimary")

        if isinstance(raw, int) and raw > 0:
            return raw

        settings = cls.bundle().get("settings")

        if isinstance(settings, dict):
            nested = settings.get("maxPrimary")

            if isinstance(nested, int) and nested > 0:
                return nested

        return 4

    @classmethod
    def label_set(cls, key: str) -> frozenset[str]:
        raw = cls.bundle().get(key)

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item or "").strip())

    @classmethod
    def disabled_reason(cls, key: str, *, default: str = "") -> str:
        reasons = cls.bundle().get("disabledReasons")

        if not isinstance(reasons, dict):
            return default

        return str(reasons.get(key) or default).strip()

    @classmethod
    def node(cls, *path: str) -> Any:
        node = cls.bundle()

        for key in path:
            if not isinstance(node, dict):
                return None

            node = node.get(key)

        return node
