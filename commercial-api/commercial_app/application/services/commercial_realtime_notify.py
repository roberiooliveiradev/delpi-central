from __future__ import annotations

import re
from typing import Any, Literal, Sequence

from commercial_app.application.services.commercial_realtime_hub import (
    commercial_realtime_hub,
)
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)
from commercial_app.domain.services.seller_portfolio_messages_content_service import (
    SellerPortfolioMessagesContentService,
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


def member_user_ids_for_customer(
    portfolios: Sequence[Any],
    *,
    customer_code: str,
    customer_store: str,
) -> list[str]:
    """Membros ativos das carteiras que possuem o cliente (code/store)."""
    code = (customer_code or "").strip()
    store = (customer_store or "").strip()
    if not code or not store:
        return []
    seen: set[str] = set()
    members: list[str] = []
    for portfolio in portfolios:
        if not getattr(portfolio, "active", True):
            continue
        customers = getattr(portfolio, "customers", ()) or ()
        if not any(
            (item.customer_code or "").strip() == code
            and (item.customer_store or "").strip() == store
            for item in customers
        ):
            continue
        for member in getattr(portfolio, "members", ()) or ():
            uid = (getattr(member, "user_id", None) or "").strip()
            if uid and uid not in seen:
                seen.add(uid)
                members.append(uid)
        owner = (getattr(portfolio, "user_id", None) or "").strip()
        if owner and owner not in seen:
            seen.add(owner)
            members.append(owner)
    return members


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def _safe_label(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    if not cleaned or _UUID_RE.match(cleaned):
        return None
    return cleaned


def resolve_user_display_name(user_id: str | None) -> str:
    """
    Fallback genérico quando o request não enviou display name.

    Não usa `display_name` da carteira (é o nome da carteira, não da pessoa).
    O nome real vem de `actor_display_name` (JWT) ou do lookup de diretório no MFE.
    """
    cleaned = (user_id or "").strip()
    if not cleaned:
        return "Alguém da equipe"
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
    actor = _safe_label(actor_display_name) or "Alguém da equipe"
    assignee = _safe_label(assignee_display_name) or "alguém"
    return {
        "title": title,
        "message": template.format(actor=actor, title=label, assignee=assignee),
        "variant": variant,
    }


def build_portfolio_notification(
    *,
    reason: str,
    display_name: str | None = None,
    actor_display_name: str | None = None,
) -> dict[str, str]:
    content = SellerPortfolioMessagesContentService
    actor = _safe_label(actor_display_name) or "Alguém da equipe"
    label = _safe_label(display_name) or "carteira"
    template = content.realtime_message_template(reason)
    try:
        message = template.format(actor=actor, display_name=label)
    except Exception:
        message = f"{actor} alterou a carteira «{label}»."
    return {
        "title": content.realtime_title(reason),
        "message": message,
        "variant": content.realtime_tone(reason),
    }


def _notification_variant(tone: str | None) -> str:
    normalized = (tone or "").strip().lower()
    if normalized in {"success", "warning", "error", "info"}:
        return normalized
    if normalized in {"danger", "destructive"}:
        return "warning"
    return "info"


def build_account_notification(
    *,
    reason: str,
    actor_display_name: str | None = None,
    payload: dict | None = None,
) -> dict[str, str]:
    content = AuditMessagesContentService
    actor = _safe_label(actor_display_name) or "Alguém da equipe"
    safe_payload = {
        key: ("" if value is None else value)
        for key, value in (payload or {}).items()
    }
    safe_payload.setdefault("action", reason)
    template = content.message_template_for(reason)
    try:
        detail = template.format(**safe_payload)
    except Exception:
        detail = f"Alteração na conta ({reason})."
    return {
        "title": content.title_for(reason),
        "message": f"{actor}: {detail}",
        "variant": _notification_variant(content.tone_for(reason)),
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


def notify_portfolio_changed(
    *,
    reason: str,
    portfolio_id: str,
    member_user_ids: Sequence[str],
    portfolio_ids: Sequence[str] | None = None,
    display_name: str | None = None,
    actor_user_id: str | None = None,
    actor_display_name: str | None = None,
    actor_client_id: str | None = None,
) -> None:
    """Broadcast para salas `user:` dos membros e para a sala `team` (gestores)."""
    members = [uid.strip() for uid in member_user_ids if uid and str(uid).strip()]
    primary_id = (portfolio_id or "").strip()
    if not members and not primary_id:
        return
    actor_label = (
        _safe_label(actor_display_name) or resolve_user_display_name(actor_user_id)
    )
    portfolio_label = _safe_label(display_name) or "carteira"
    related = [
        pid.strip()
        for pid in (portfolio_ids or [])
        if pid and str(pid).strip()
    ]
    if primary_id and primary_id not in related:
        related = [primary_id, *related]
    notification = build_portfolio_notification(
        reason=reason,
        display_name=portfolio_label,
        actor_display_name=actor_label,
    )
    payload = {
        "type": "portfolio.changed",
        "reason": reason,
        "portfolioId": primary_id or None,
        "portfolioIds": related,
        "displayName": portfolio_label,
        "memberUserIds": members,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorDisplayName": actor_label,
        "actorClientId": (actor_client_id or "").strip() or None,
        "notification": notification,
    }
    rooms = {user_room(uid) for uid in members}
    rooms.add(TEAM_ROOM)
    for room in rooms:
        commercial_realtime_hub.schedule_broadcast(room, payload)


def notify_account_changed(
    *,
    reason: str,
    customer_code: str,
    customer_store: str,
    member_user_ids: Sequence[str] | None = None,
    actor_user_id: str | None = None,
    actor_display_name: str | None = None,
    actor_client_id: str | None = None,
    payload: dict | None = None,
) -> None:
    """Broadcast para salas `user:` dos membros das carteiras do cliente e `team`."""
    code = (customer_code or "").strip()
    store = (customer_store or "").strip()
    if not code or not store:
        return
    members = [uid.strip() for uid in (member_user_ids or ()) if uid and str(uid).strip()]
    actor = (actor_user_id or "").strip()
    if actor and actor not in members:
        members.append(actor)
    actor_label = (
        _safe_label(actor_display_name) or resolve_user_display_name(actor_user_id)
    )
    notification = build_account_notification(
        reason=reason,
        actor_display_name=actor_label,
        payload=payload,
    )
    body = {
        "type": "account.changed",
        "reason": reason,
        "customerCode": code,
        "customerStore": store,
        "memberUserIds": members,
        "actorUserId": actor or None,
        "actorDisplayName": actor_label,
        "actorClientId": (actor_client_id or "").strip() or None,
        "notification": notification,
    }
    rooms = {user_room(uid) for uid in members}
    rooms.add(TEAM_ROOM)
    for room in rooms:
        commercial_realtime_hub.schedule_broadcast(room, body)
