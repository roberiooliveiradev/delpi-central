"""Notificações in-app Auditoria 5S via Core API (sino do portal)."""

from __future__ import annotations

import html
import logging
import re
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "auditoria-5s"
_CATEGORY = "auditoria_5s"
_APP_BASE = "/apps/auditoria-5s"
_EVENT_RESPONSIBLE_ASSIGNED = "audit_5s_nc_responsible_assigned"
_EVENT_NOTE_MENTION = "audit_5s_nc_note_mention"
_NOTE_MESSAGE_MAX = 2000


def audit_5s_portal_notifications_enabled() -> bool:
    if not settings.AUDIT_5S_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def branch_portal_route(branch_code: str | None) -> str:
    code = str(branch_code or "").strip()
    filial = "filial-02" if code == "02" else "filial-01"
    # Deep link: filial + tela de gestão de NCs (MFE lê /nc-board no pathname).
    return f"{_APP_BASE}/{filial}/nc-board"


def responsible_assigned_dedupe_key(*, nc_id: str, user_id: str) -> str:
    return f"audit5s:nc_responsible:{nc_id}:{user_id}"


def note_mention_dedupe_key(*, action_id: str, user_id: str) -> str:
    return f"audit5s:nc_mention:{action_id}:{user_id}"


def action_label_for_nc(*, corrective_action: str | None, description: str | None) -> str:
    corrective = (corrective_action or "").strip()
    if corrective:
        return corrective
    fallback = (description or "").strip()
    return fallback or "plano de ação"


def should_notify_note_mention(
    *,
    mentioned_user_id: str | None,
    actor_user_id: str | None = None,
) -> bool:
    normalized = (mentioned_user_id or "").strip()
    if not normalized or normalized == "unknown":
        return False
    actor = (actor_user_id or "").strip()
    if actor and actor == normalized:
        return False
    return True


def should_notify_responsible_assignment(
    *,
    previous_user_id: str | None,
    new_user_id: str | None,
    actor_user_id: str | None = None,
) -> bool:
    normalized_new = (new_user_id or "").strip()
    if not normalized_new or normalized_new == "unknown":
        return False
    normalized_previous = (previous_user_id or "").strip()
    if normalized_previous == normalized_new:
        return False
    normalized_actor = (actor_user_id or "").strip()
    if normalized_actor and normalized_actor == normalized_new:
        return False
    return True


def send_audit_5s_portal_notification(
    *,
    recipient_user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    action_label: str = "Abrir gestão de NCs",
    action_target: str,
    dedupe_key: str,
    event_type: str,
    metadata: dict[str, Any] | None = None,
    presentation: str = "text",
    html_content: str | None = None,
) -> bool:
    if not audit_5s_portal_notifications_enabled():
        return False

    if not recipient_user_id or recipient_user_id.strip() in {"", "unknown"}:
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
    payload: dict[str, Any] = {
        "userIds": [recipient_user_id.strip()],
        "title": title,
        "message": message,
        "type": notification_type,
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": action_label,
            "target": action_target,
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": event_type,
            "dedupeKey": dedupe_key,
            **(metadata or {}),
        },
    }
    normalized_presentation = (presentation or "text").strip().lower()
    if normalized_presentation and normalized_presentation != "text":
        payload["presentation"] = normalized_presentation
    if html_content and html_content.strip():
        payload["presentation"] = "html"
        payload["htmlContent"] = html_content.strip()

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                f"{base_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code in (200, 201, 202):
            return True
        body_preview = (response.text or "")[:500]
        logger.warning(
            "audit_5s_portal_notification_rejected status=%s event=%s user=%s body=%s",
            response.status_code,
            event_type,
            recipient_user_id,
            body_preview,
        )
    except Exception:
        logger.warning(
            "audit_5s_portal_notification_failed event=%s user=%s",
            event_type,
            recipient_user_id,
            exc_info=True,
        )
    return False


_PRIORITY_LABELS = {
    "high": "Alta",
    "medium": "Média",
    "low": "Baixa",
}


def _priority_label(priority: str | None) -> str | None:
    raw = (priority or "").strip().lower()
    if not raw:
        return None
    return _PRIORITY_LABELS.get(raw, raw)


def _format_due_date(due_date: str | None) -> str | None:
    raw = str(due_date or "").strip()
    if not raw:
        return None
    # YYYY-MM-DD or datetime prefix
    date_part = raw[:10]
    if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
        year, month, day = date_part.split("-")
        return f"{day}/{month}/{year}"
    return raw


def build_responsible_assigned_copy(
    *,
    actor_name: str | None = None,
    corrective_action: str | None = None,
    description: str | None = None,
    root_cause: str | None = None,
    audit_code: str | None = None,
    area_name: str | None = None,
    criterion_code: str | None = None,
    criterion_description: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
) -> tuple[str, str, str]:
    actor = (actor_name or "").strip() or "alguém"
    action = action_label_for_nc(
        corrective_action=corrective_action,
        description=description,
    )
    title = f'Você foi designado responsável pela ação "{action}"'

    detail_lines: list[tuple[str, str]] = [("Ação", action)]
    description_text = (description or "").strip()
    if description_text and description_text != action:
        detail_lines.append(("Problema / NC", description_text))
    root_cause_text = (root_cause or "").strip()
    if root_cause_text:
        detail_lines.append(("Causa raiz", root_cause_text))
    area_text = (area_name or "").strip()
    if area_text:
        detail_lines.append(("Área", area_text))
    criterion_code_text = (criterion_code or "").strip()
    criterion_desc_text = (criterion_description or "").strip()
    if criterion_code_text or criterion_desc_text:
        criterion_value = (
            f"{criterion_code_text} — {criterion_desc_text}"
            if criterion_code_text and criterion_desc_text
            else criterion_code_text or criterion_desc_text
        )
        detail_lines.append(("Critério", criterion_value))
    audit_text = (audit_code or "").strip()
    if audit_text:
        detail_lines.append(("Auditoria", audit_text))
    due_label = _format_due_date(due_date)
    if due_label:
        detail_lines.append(("Prazo", due_label))
    priority_label = _priority_label(priority)
    if priority_label:
        detail_lines.append(("Prioridade", priority_label))

    plain_details = "\n".join(f"{label}: {value}" for label, value in detail_lines)
    message = (
        f'Você foi designado por {actor} como responsável pela ação "{action}".\n\n'
        f"{plain_details}"
    )

    safe_actor = html.escape(actor)
    safe_action = html.escape(action)
    list_items = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(value)}</li>"
        for label, value in detail_lines
    )
    html_content = (
        f"<p>Você foi designado por <strong>{safe_actor}</strong> "
        f'como responsável pela ação &ldquo;{safe_action}&rdquo;:</p>'
        f'<span class="notification-note-bubble"><ul>{list_items}</ul></span>'
    )
    return title, message, html_content


def notify_nc_responsible_assigned(
    *,
    nc_id: str,
    recipient_user_id: str,
    branch_code: str | None,
    audit_code: str | None = None,
    criterion_code: str | None = None,
    criterion_description: str | None = None,
    area_name: str | None = None,
    corrective_action: str | None = None,
    description: str | None = None,
    root_cause: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    previous_user_id: str | None = None,
    actor_user_id: str | None = None,
    actor_name: str | None = None,
) -> bool:
    if not should_notify_responsible_assignment(
        previous_user_id=previous_user_id,
        new_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
    ):
        return False

    title, message, html_content = build_responsible_assigned_copy(
        actor_name=actor_name,
        corrective_action=corrective_action,
        description=description,
        root_cause=root_cause,
        audit_code=audit_code,
        area_name=area_name,
        criterion_code=criterion_code,
        criterion_description=criterion_description,
        due_date=due_date,
        priority=priority,
    )

    return send_audit_5s_portal_notification(
        recipient_user_id=recipient_user_id,
        title=title,
        message=message,
        notification_type="info",
        action_label="Abrir gestão de NCs",
        action_target=branch_portal_route(branch_code),
        dedupe_key=responsible_assigned_dedupe_key(
            nc_id=nc_id,
            user_id=recipient_user_id.strip(),
        ),
        event_type=_EVENT_RESPONSIBLE_ASSIGNED,
        metadata={
            "ncId": nc_id,
            "branchCode": branch_code,
            "auditCode": audit_code,
            "criterionCode": criterion_code,
            "actionLabel": action_label_for_nc(
                corrective_action=corrective_action,
                description=description,
            ),
        },
        html_content=html_content,
    )


def _clip_note_text(note_text: str) -> str:
    text = (note_text or "").strip()
    if len(text) <= _NOTE_MESSAGE_MAX:
        return text
    return f"{text[: _NOTE_MESSAGE_MAX - 1].rstrip()}…"


_MENTION_TOKEN_RE = re.compile(
    r"@([A-ZÀ-Ý][\wÀ-ÿ'’.-]*(?:\s+(?:(?:de|da|do|das|dos|e)|[A-ZÀ-Ý][\wÀ-ÿ'’.-]*))*)",
    re.UNICODE,
)


def format_note_text_plain_without_at(note_text: str) -> str:
    """Remove o @ das menções no texto plano da notificação."""
    return _MENTION_TOKEN_RE.sub(r"\1", note_text or "")


def format_note_text_html_with_mentions(note_text: str) -> str:
    """HTML seguro: menções em negrito sem @, restante escapado."""
    source = note_text or ""
    parts: list[str] = []
    last = 0
    for match in _MENTION_TOKEN_RE.finditer(source):
        if match.start() > last:
            parts.append(html.escape(source[last : match.start()]).replace("\n", "<br />"))
        name = (match.group(1) or "").strip()
        if name:
            parts.append(f"<strong>{html.escape(name)}</strong>")
        last = match.end()
    if last < len(source):
        parts.append(html.escape(source[last:]).replace("\n", "<br />"))
    return "".join(parts) if parts else html.escape(source).replace("\n", "<br />")


def build_note_mention_copy(
    *,
    actor_name: str | None,
    action_label: str,
    note_text: str,
) -> tuple[str, str, str]:
    actor = (actor_name or "").strip() or "alguém"
    label = (action_label or "").strip() or "plano de ação"
    note = _clip_note_text(note_text)
    note_plain = format_note_text_plain_without_at(note)
    title = f"Você foi mencionado por {actor}"
    message = (
        f'Você foi mencionado por {actor} na ação "{label}":\n\n{note_plain}'
    )
    safe_actor = html.escape(actor)
    safe_label = html.escape(label)
    safe_note = format_note_text_html_with_mentions(note)
    html_content = (
        f"<p>Você foi mencionado por <strong>{safe_actor}</strong> "
        f'na ação &ldquo;{safe_label}&rdquo;:</p>'
        f'<span class="notification-note-bubble">{safe_note}</span>'
    )
    return title, message, html_content


def notify_nc_note_mentions(
    *,
    nc_id: str,
    action_id: str,
    mentioned_user_ids: list[str] | None,
    note_text: str,
    branch_code: str | None,
    action_label: str,
    actor_user_id: str | None = None,
    actor_name: str | None = None,
    audit_code: str | None = None,
) -> int:
    """Notifica usuários mencionados em uma nota do histórico da NC.

    Retorna quantas notificações foram aceitas pelo Core API.
    """
    unique_ids: list[str] = []
    seen: set[str] = set()
    for raw in mentioned_user_ids or []:
        uid = str(raw or "").strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        unique_ids.append(uid)

    if not unique_ids or not (note_text or "").strip():
        return 0

    title, message, html_content = build_note_mention_copy(
        actor_name=actor_name,
        action_label=action_label,
        note_text=note_text,
    )
    sent = 0
    for user_id in unique_ids:
        if not should_notify_note_mention(
            mentioned_user_id=user_id,
            actor_user_id=actor_user_id,
        ):
            continue
        ok = send_audit_5s_portal_notification(
            recipient_user_id=user_id,
            title=title,
            message=message,
            notification_type="info",
            action_label="Abrir gestão de NCs",
            action_target=branch_portal_route(branch_code),
            dedupe_key=note_mention_dedupe_key(
                action_id=action_id,
                user_id=user_id,
            ),
            event_type=_EVENT_NOTE_MENTION,
            metadata={
                "ncId": nc_id,
                "actionId": action_id,
                "branchCode": branch_code,
                "auditCode": audit_code,
            },
            html_content=html_content,
        )
        if ok:
            sent += 1
    return sent
