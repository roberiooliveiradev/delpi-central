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

_NOTIFICATION_BY_REASON: dict[WorklistChangeReason, tuple[str, str, str]] = {
    # title, message_template (usa {title}), variant
    "task.created": ("Nova tarefa", "Foi atribuída a você (ou à equipe): {title}", "info"),
    "task.updated": ("Tarefa atualizada", "Alteração na fila: {title}", "info"),
    "task.completed": ("Tarefa concluída", "Concluída: {title}", "success"),
    "task.deferred": ("Prazo adiado", "Adiada em +1 dia: {title}", "warning"),
    "task.reassigned": ("Tarefa reatribuída", "Responsável alterado: {title}", "info"),
    "attachment.changed": ("Anexo na tarefa", "Anexo alterado em: {title}", "info"),
}


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def build_worklist_notification(
    *,
    reason: WorklistChangeReason,
    task_title: str | None,
) -> dict[str, str]:
    title, template, variant = _NOTIFICATION_BY_REASON[reason]
    label = (task_title or "").strip() or "Tarefa sem título"
    return {
        "title": title,
        "message": template.format(title=label),
        "variant": variant,
    }


def notify_worklist_changed(
    *,
    reason: WorklistChangeReason,
    task_id: str,
    assignee_user_ids: list[str],
    actor_client_id: str | None = None,
    actor_user_id: str | None = None,
    task_title: str | None = None,
) -> None:
    notification = build_worklist_notification(reason=reason, task_title=task_title)
    payload = {
        "type": "worklist.changed",
        "reason": reason,
        "taskId": task_id,
        "taskTitle": (task_title or "").strip() or None,
        "assigneeUserIds": [uid for uid in assignee_user_ids if uid and uid.strip()],
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorClientId": (actor_client_id or "").strip() or None,
        "notification": notification,
    }
    rooms: set[str] = {TEAM_ROOM}
    for uid in assignee_user_ids:
        cleaned = (uid or "").strip()
        if cleaned:
            rooms.add(user_room(cleaned))
    for room in rooms:
        commercial_realtime_hub.schedule_broadcast(room, payload)
