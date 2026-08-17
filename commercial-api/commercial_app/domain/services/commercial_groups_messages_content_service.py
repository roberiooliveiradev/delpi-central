from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "commercial_groups_messages.json"
)


@lru_cache(maxsize=1)
def load_commercial_groups_messages() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("commercial_groups_messages.json deve ser um objeto.")
    return payload


class CommercialGroupsMessagesContentService:
    """Loader canônico de textos PT-BR de grupos operacionais."""

    @classmethod
    def clear_cache(cls) -> None:
        load_commercial_groups_messages.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_commercial_groups_messages()

    @classmethod
    def error(cls, key: str, **values: str) -> str:
        errors = cls.bundle().get("errors") or {}
        template = str(errors.get(key) or key)
        if not values:
            return template
        try:
            return template.format(**values)
        except Exception:
            return template

    @classmethod
    def message(cls, key: str) -> str:
        messages = cls.bundle().get("messages") or {}
        return str(messages.get(key) or key)
