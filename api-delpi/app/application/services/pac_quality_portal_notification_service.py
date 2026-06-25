"""Notificações in-app PAC Qualidade via Core API (Onda 4.1)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PAC_SOURCE_APP = "quality-action-plans"
_PAC_APP_BASE = "/apps/quality-action-plans"


def pac_portal_notifications_enabled() -> bool:
    if not settings.PAC_QUALITY_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def _plan_detail_route(plan_id: str) -> str:
    return f"{_PAC_APP_BASE}/plano/{plan_id}"


def send_pac_portal_notification(
    *,
    recipient_user_id: str,
    title: str,
    message: str,
    notification_type: str = "warning",
    action_label: str = "Abrir plano",
    action_target: str,
    dedupe_key: str,
    event_type: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if not pac_portal_notifications_enabled():
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
        "category": "quality",
        "sourceApp": _PAC_SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": action_label,
            "target": action_target,
        },
        "metadata": {
            "source": _PAC_SOURCE_APP,
            "event": event_type,
            "dedupeKey": dedupe_key,
            **(metadata or {}),
        },
    }

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
        logger.warning(
            "pac_portal_notification_rejected status=%s event=%s user=%s",
            response.status_code,
            event_type,
            recipient_user_id,
        )
    except Exception:
        logger.warning(
            "pac_portal_notification_failed event=%s user=%s",
            event_type,
            recipient_user_id,
            exc_info=True,
        )
    return False


def build_action_due_notification(
    *,
    action_id: str,
    plan_id: str,
    plan_code: str | None,
    action_description: str | None,
    due_date: str,
    recipient_user_id: str,
    dedupe_key: str,
) -> dict[str, Any]:
    code = plan_code or plan_id
    description = (action_description or "Ação do plano").strip()
    return {
        "recipient_user_id": recipient_user_id,
        "title": "Ação PAC vencendo em breve",
        "message": (
            f"Plano {code}: «{description}» vence em {due_date}. "
            "Revise o prazo ou conclua a ação."
        ),
        "notification_type": "warning",
        "action_label": "Ver plano",
        "action_target": _plan_detail_route(plan_id),
        "dedupe_key": dedupe_key,
        "event_type": "pac_action_due_soon",
        "metadata": {
            "planId": plan_id,
            "actionId": action_id,
            "dueDate": due_date,
        },
    }


def build_plan_stalled_notification(
    *,
    plan_id: str,
    plan_code: str | None,
    plan_title: str | None,
    days_without_update: int,
    recipient_user_id: str,
    dedupe_key: str,
) -> dict[str, Any]:
    code = plan_code or plan_id
    title_text = (plan_title or "").strip()
    detail = f" · {title_text}" if title_text else ""
    return {
        "recipient_user_id": recipient_user_id,
        "title": "Plano crítico sem movimento",
        "message": (
            f"Plano {code}{detail} está parado há {days_without_update} dia(s). "
            "Coordenação deve acompanhar o andamento."
        ),
        "notification_type": "error",
        "action_label": "Abrir plano",
        "action_target": _plan_detail_route(plan_id),
        "dedupe_key": dedupe_key,
        "event_type": "pac_plan_stalled",
        "metadata": {
            "planId": plan_id,
            "daysWithoutUpdate": days_without_update,
        },
    }
