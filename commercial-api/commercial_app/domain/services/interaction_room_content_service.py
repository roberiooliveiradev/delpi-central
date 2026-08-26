from __future__ import annotations

import json
import re
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
    for section in (
        "errors",
        "messages",
        "empty",
        "filters",
        "activity",
        "notifications",
        "settings",
    ):
        value = payload.get(section)
        if not isinstance(value, dict) or not value:
            raise ValueError(f"interaction_room.json precisa de {section} não vazio.")
    return payload


class InteractionRoomContentService:
    """Loader canônico de textos PT-BR da sala de interação."""

    @classmethod
    def clear_cache(cls) -> None:
        load_interaction_room_messages.cache_clear()
        cls.markdown_image_pattern.cache_clear()
        cls.allowed_attachment_image_href_pattern.cache_clear()

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

    @classmethod
    def setting_int(cls, key: str, default: int) -> int:
        raw = cls._section("settings").get(key)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def setting_str(cls, key: str, default: str = "") -> str:
        raw = cls._section("settings").get(key)
        value = str(raw or "").strip()
        return value or default

    @classmethod
    @lru_cache(maxsize=1)
    def markdown_image_pattern(cls) -> re.Pattern[str]:
        raw = cls.setting_str(
            "markdownImagePattern",
            r"!\[([^\]]*)]\(([^)]+)\)",
        )
        return re.compile(raw)

    @classmethod
    @lru_cache(maxsize=1)
    def allowed_attachment_image_href_pattern(cls) -> re.Pattern[str]:
        raw = cls.setting_str(
            "allowedAttachmentImageHrefPattern",
            r"^attachment:(?:pending:[A-Za-z0-9_-]+|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$",
        )
        return re.compile(raw)

    @classmethod
    def task_title_from_message_body(cls, body_text: str) -> str:
        limit = max(
            1,
            min(cls.setting_int("taskTitleSummaryMaxChars", 80), 200),
        )
        text = cls.markdown_image_pattern().sub("", str(body_text or ""))
        cleaned = " ".join(text.split())
        if not cleaned:
            return cls.message("taskFromMessageDefaultTitle")
        if len(cleaned) <= limit:
            return cleaned
        trimmed = cleaned[: max(1, limit - 1)].rstrip()
        return f"{trimmed}…"

    @classmethod
    def related_entity_type_room(cls) -> str:
        return cls.setting_str("relatedEntityTypeRoom", "interaction_room")

    @classmethod
    def task_ref_message_kind(cls) -> str:
        return cls.setting_str("taskRefMessageKind", "task_ref")

    @classmethod
    def task_mention_kind(cls) -> str:
        return cls.setting_str("taskMentionKind", "task")

    @classmethod
    def task_ref_body(cls, *, title: str) -> str:
        template = cls.message("taskRefBody")
        cleaned_title = " ".join(str(title or "").split()) or cls.message(
            "taskFromMessageDefaultTitle"
        )
        try:
            return template.format(title=cleaned_title)
        except Exception:
            return f"{template} {cleaned_title}".strip()

    @classmethod
    def setting_str_list(cls, key: str) -> tuple[str, ...]:
        raw = cls._section("settings").get(key)
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item or "").strip())

    @classmethod
    def system_message_kind(cls) -> str:
        return cls.setting_str("systemMessageKind", "system")

    @classmethod
    def system_event_kinds(cls) -> frozenset[str]:
        return frozenset(cls.setting_str_list("systemEventKinds"))

    @classmethod
    def is_allowed_system_event_kind(cls, event_kind: str) -> bool:
        kind = str(event_kind or "").strip()
        return bool(kind) and kind in cls.system_event_kinds()
