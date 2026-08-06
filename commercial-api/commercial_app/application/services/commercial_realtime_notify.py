from __future__ import annotations

from typing import Literal

from commercial_app.application.services.commercial_realtime_hub import (
    commercial_realtime_hub,
)

WorklistChangeReason = Literal[
    "task.created",
    "task.updated",
    "task.completed",
    "task.deferred",
    "task.reassigned",
    "attachment.changed",
]

TEAM_ROOM = "team"


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def notify_worklist_changed(
    *,
    reason: WorklistChangeReason,
    task_id: str,
    assignee_user_ids: list[str],
    actor_client_id: str | None = None,
) -> None:
    payload = {
        "type": "worklist.changed",
        "reason": reason,
        "taskId": task_id,
        "assigneeUserIds": [uid for uid in assignee_user_ids if uid and uid.strip()],
        "actorClientId": (actor_client_id or "").strip() or None,
    }
    rooms: set[str] = {TEAM_ROOM}
    for uid in assignee_user_ids:
        cleaned = (uid or "").strip()
        if cleaned:
            rooms.add(user_room(cleaned))
    for room in rooms:
        commercial_realtime_hub.schedule_broadcast(room, payload)
