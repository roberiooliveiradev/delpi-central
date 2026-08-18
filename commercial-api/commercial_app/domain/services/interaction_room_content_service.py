from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "interaction_room.json"
)


@lru_cache(maxsize=1)
def load_interaction_room_messages() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("interaction_room.json deve ser um objeto.")
    for section in ("errors", "messages", "empty", "filters", "activity"):
        value = payload.get(section)
        if not isinstance(value, dict) or not value:
            raise ValueError(f"interaction_room.json precisa de {section} não vazio.")
    return payload


class InteractionRoomContentService:
    """Loader canônico de textos PT-BR da sala de interação."""

    @classmethod
    def clear_cache(cls) -> None:
        load_interaction_room_messages.cache_clear()

    @classmethod
    def bundle(cls) -> dict[str, Any]:
        return load_interaction_room_messages()

    @classmethod
    def _section(cls, name: str) -> dict[str, Any]:
        section = cls.bundle().get(name) or {}
        return section if isinstance(section, dict) else {}

    @classmethod
    def error(cls, key: str, **values: str) -> str:
        template = str(cls._section("errors").get(key) or key)
        if not values:
            return template
        try:
            return template.format(**values)
        except Exception:
            return template

    @classmethod
    def message(cls, key: str) -> str:
        return str(cls._section("messages").get(key) or key)

    @classmethod
    def empty(cls, key: str) -> str:
        return str(cls._section("empty").get(key) or key)

    @classmethod
    def filter_label(cls, key: str) -> str:
        return str(cls._section("filters").get(key) or key)

    @classmethod
    def activity(cls, key: str) -> str:
        return str(cls._section("activity").get(key) or key)
