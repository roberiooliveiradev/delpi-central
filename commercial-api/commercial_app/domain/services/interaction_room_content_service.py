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
    for section in ("errors", "messages", "empty", "filters", "activity", "notifications"):
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

    @classmethod
    def notification(cls, key: str) -> dict[str, Any]:
        block = cls._section("notifications").get(key) or {}
        return block if isinstance(block, dict) else {}

    @classmethod
    def mention_event_type(cls) -> str:
        return str(
            cls.notification("mention").get("eventType")
            or "commercial.interaction.mention"
        ).strip()

    @classmethod
    def mention_category(cls) -> str:
        return str(
            cls.notification("mention").get("category") or "commercial_collaboration"
        ).strip()

    @classmethod
    def format_mention_message(cls, *, actor: str, excerpt: str) -> str:
        block = cls.notification("mention")
        template = str(block.get("messageTemplate") or "{actor}: {excerpt}")
        try:
            return template.format(actor=actor, excerpt=excerpt)
        except Exception:
            return f"{actor}: {excerpt}"

    @classmethod
    def mention_excerpt(cls, body_text: str) -> str:
        block = cls.notification("mention")
        try:
            limit = int(block.get("excerptMaxChars") or 80)
        except (TypeError, ValueError):
            limit = 80
        limit = max(20, min(limit, 200))
        cleaned = " ".join(str(body_text or "").split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: max(1, limit - 1)].rstrip() + "…"

    @classmethod
    def mention_deep_link(cls, *, room_id: str) -> str:
        block = cls.notification("mention")
        template = str(
            block.get("deepLinkTemplate")
            or "/apps/commercial/interaction-rooms/{roomId}"
        )
        try:
            return template.format(roomId=str(room_id or "").strip())
        except Exception:
            return f"/apps/commercial/interaction-rooms/{str(room_id or '').strip()}"
