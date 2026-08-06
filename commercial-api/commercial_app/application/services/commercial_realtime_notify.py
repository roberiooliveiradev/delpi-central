from __future__ import annotations

import re
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
    "task.deleted",
    "attachment.changed",
]

Audience = Literal["assignee", "previous", "team"]

TEAM_ROOM = "team"

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# title, message_template ({actor}, {title}, {assignee}), variant
_NOTIFICATION_BY_REASON: dict[WorklistChangeReason, dict[Audience, tuple[str, str, str]]] = {
    "task.created": {
        "assignee": ("Nova tarefa", "{actor} atribuiu a você: {title}", "info"),
        "previous": ("Nova tarefa", "{actor} atribuiu a {assignee}: {title}", "info"),
        "team": ("Nova tarefa", "{actor} atribuiu a {assignee}: {title}", "info"),
    },
    "task.updated": {
        "assignee": ("Tarefa atualizada", "{actor} alterou a tarefa: {title}", "info"),
        "previous": ("Tarefa atualizada", "{actor} alterou a tarefa: {title}", "info"),
        "team": ("Tarefa atualizada", "{actor} alterou a tarefa: {title}", "info"),
    },
    "task.completed": {
        "assignee": ("Tarefa concluída", "{actor} concluiu: {title}", "success"),
        "previous": ("Tarefa concluída", "{actor} concluiu: {title}", "success"),
        "team": ("Tarefa concluída", "{actor} concluiu: {title}", "success"),
    },
    "task.deferred": {
        "assignee": ("Prazo adiado", "{actor} adiou o prazo: {title}", "warning"),
        "previous": ("Prazo adiado", "{actor} adiou o prazo: {title}", "warning"),
        "team": ("Prazo adiado", "{actor} adiou o prazo: {title}", "warning"),
    },
    "task.reassigned": {
        "assignee": ("Tarefa reatribuída", "{actor} atribuiu a você: {title}", "info"),
        "previous": ("Tarefa reatribuída", "{actor} reatribuiu a {assignee}: {title}", "info"),
        "team": ("Tarefa reatribuída", "{actor} reatribuiu a {assignee}: {title}", "info"),
    },
    "task.deleted": {
        "assignee": ("Tarefa excluída", "{actor} excluiu: {title}", "warning"),
        "previous": ("Tarefa excluída", "{actor} excluiu: {title}", "warning"),
        "team": ("Tarefa excluída", "{actor} excluiu: {title}", "warning"),
    },
    "attachment.changed": {
        "assignee": ("Anexo na tarefa", "{actor} alterou anexo em: {title}", "info"),
        "previous": ("Anexo na tarefa", "{actor} alterou anexo em: {title}", "info"),
        "team": ("Anexo na tarefa", "{actor} alterou anexo em: {title}", "info"),
    },
}


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def _safe_label(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    if not cleaned or _UUID_RE.match(cleaned):
        return None
    return cleaned


def resolve_user_display_name(user_id: str | None) -> str:
    """Nome amigável via carteira; nunca devolve UUID."""
    cleaned = (user_id or "").strip()
    if not cleaned:
        return "Alguém"
    try:
        from commercial_app.composition.commercial_composer import (
            build_seller_portfolio_repository,
        )

        portfolio = build_seller_portfolio_repository().get_by_user_id(cleaned)
        name = _safe_label(portfolio.display_name if portfolio else None)
        if name:
            return name
    except Exception:  # noqa: BLE001 — notify não pode falhar a mutação
        pass
    return "Alguém da equipe"


def resolve_actor_display_name(actor_user_id: str | None) -> str:
    """Compat: mesmo critério de resolve_user_display_name."""
    return resolve_user_display_name(actor_user_id)


def build_worklist_notification(
    *,
    reason: WorklistChangeReason,
    task_title: str | None,
    actor_display_name: str | None = None,
    assignee_display_name: str | None = None,
    audience: Audience = "team",
) -> dict[str, str]:
    title, template, variant = _NOTIFICATION_BY_REASON[reason][audience]
    label = (task_title or "").strip() or "Tarefa sem título"
    actor = _safe_label(actor_display_name) or "Alguém"
    assignee = _safe_label(assignee_display_name) or "alguém"
    return {
        "title": title,
        "message": template.format(actor=actor, title=label, assignee=assignee),
        "variant": variant,
    }


def notify_worklist_changed(
    *,
    reason: WorklistChangeReason,
    task_id: str,
    assignee_user_ids: list[str],
    actor_client_id: str | None = None,
    actor_user_id: str | None = None,
    actor_display_name: str | None = None,
    assignee_display_name: str | None = None,
    task_title: str | None = None,
) -> None:
    """
    Um payload por broadcast (team + user rooms).

    A personalização «atribuiu a você» é feita no MFE com base em
    `assigneeUserIds` + usuário logado — evita toast duplicado em gestores
    que estão em `user:` e `team`.
    """
    assignees = [uid.strip() for uid in assignee_user_ids if uid and uid.strip()]
    actor_label = (
        _safe_label(actor_display_name) or resolve_user_display_name(actor_user_id)
    )
    current_assignee_id = assignees[0] if assignees else None
    assignee_label = (
        _safe_label(assignee_display_name)
        or resolve_user_display_name(current_assignee_id)
    )
    # Mensagem «team» no fio; MFE troca para assignee/previous quando couber.
    notification = build_worklist_notification(
        reason=reason,
        task_title=task_title,
        actor_display_name=actor_label,
        assignee_display_name=assignee_label,
        audience="team",
    )
    payload = {
        "type": "worklist.changed",
        "reason": reason,
        "taskId": task_id,
        "taskTitle": (task_title or "").strip() or None,
        "assigneeUserIds": assignees,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorDisplayName": actor_label,
        "assigneeDisplayName": assignee_label,
        "actorClientId": (actor_client_id or "").strip() or None,
        "notification": notification,
    }
    rooms: set[str] = {TEAM_ROOM}
    for uid in assignees:
        rooms.add(user_room(uid))
    for room in rooms:
        commercial_realtime_hub.schedule_broadcast(room, payload)
