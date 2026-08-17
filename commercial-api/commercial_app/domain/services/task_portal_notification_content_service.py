"""Content loader for commercial task portal notifications."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "task_portal_notification.json"
)

EVENT_ASSIGNED = "commercial.task.assigned"
EVENT_GROUP_ASSIGNED = "commercial.task.group_assigned"
EVENT_COMPLETED = "commercial.task.completed"
EVENT_DUE_SOON = "commercial.task.due_soon"
EVENT_OVERDUE = "commercial.task.overdue"

TASK_PORTAL_EVENT_TYPES = frozenset(
    {
        EVENT_ASSIGNED,
        EVENT_GROUP_ASSIGNED,
        EVENT_COMPLETED,
        EVENT_DUE_SOON,
        EVENT_OVERDUE,
    }
)

_DEFAULT_DEEP_LINK = "/apps/commercial/my-tasks"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


class TaskPortalNotificationContentService:
    @classmethod
    def raw(cls) -> dict[str, Any]:
        return dict(_load())

    @classmethod
    def category(cls) -> str:
        return str(_load().get("category") or "commercial_tasks").strip() or "commercial_tasks"

    @classmethod
    def source_app(cls) -> str:
        return str(_load().get("sourceApp") or "commercial").strip() or "commercial"

    @classmethod
    def aggregate_type(cls) -> str:
        return (
            str(_load().get("aggregateType") or "commercial_task").strip()
            or "commercial_task"
        )

    @classmethod
    def due_soon_hours(cls) -> int:
        raw = _load().get("dueSoonHours")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return 24
        return max(1, min(value, 168))

    @classmethod
    def due_checkpoint_source_key(cls) -> str:
        value = str(_load().get("dueCheckpointSourceKey") or "").strip()
        return value or "commercial.tasks.due_notifications"

    @classmethod
    def action_label(cls) -> str:
        return str(_load().get("actionLabel") or "Abrir tarefas").strip() or "Abrir tarefas"

    @classmethod
    def event_block(cls, event_type: str) -> dict[str, Any]:
        events = _load().get("events")
        if not isinstance(events, dict):
            return {}
        block = events.get(event_type)
        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def format_due_label(cls, due_at_iso: str | None) -> str:
        raw = (due_at_iso or "").strip()
        if not raw:
            return "sem prazo"
        # Keep date portion readable when ISO.
        if "T" in raw:
            return raw.split("T", 1)[0]
        return raw[:16]

    @classmethod
    def format_message(cls, event_type: str, *, title: str, due_at_iso: str | None = None) -> str:
        block = cls.event_block(event_type)
        template = str(block.get("messageTemplate") or "{title}").strip() or "{title}"
        return template.format(
            title=(title or "Tarefa").strip() or "Tarefa",
            due=cls.format_due_label(due_at_iso),
        )

    @classmethod
    def title_for(cls, event_type: str) -> str:
        block = cls.event_block(event_type)
        return str(block.get("title") or "Atualização de tarefa").strip()

    @classmethod
    def notification_type_for(cls, event_type: str) -> str:
        block = cls.event_block(event_type)
        value = str(block.get("type") or "info").strip() or "info"
        return value

    @classmethod
    def bucket_for(cls, event_type: str) -> str:
        block = cls.event_block(event_type)
        return str(block.get("bucket") or "today").strip() or "today"

    @classmethod
    def build_deep_link_path(
        cls,
        *,
        bucket: str | None = None,
        search: str | None = None,
    ) -> str:
        base = str(_load().get("deepLinkPath") or _DEFAULT_DEEP_LINK).strip() or _DEFAULT_DEEP_LINK
        split = urlsplit(base)
        query = dict(parse_qsl(split.query, keep_blank_values=True))
        query.pop("view", None)
        bucket_s = (bucket or "").strip()
        search_s = (search or "").strip()
        if bucket_s:
            query["bucket"] = bucket_s
        if search_s:
            query["q"] = search_s
        return urlunsplit(
            (split.scheme, split.netloc, split.path, urlencode(query), split.fragment)
        )
