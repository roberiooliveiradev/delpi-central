"""Notificações in-app do Central de Agendamento via Core API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.application.security.api_delpi_permissions import SCHEDULING_BRANCH_APPROVE_PERMS
from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "central-agendamento"
_CATEGORY = "central_agendamento"
_APP_BASE = "/apps/central-agendamento"


def scheduling_portal_notifications_enabled() -> bool:
    if not settings.SCHEDULING_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def _branch_path_suffix(branch_code: str) -> str:
    return f"filial-{branch_code.lower()}"


def approvals_portal_route(branch_code: str, booking_id: str) -> str:
    return (
        f"{_APP_BASE}/{_branch_path_suffix(branch_code)}"
        f"?tab=approvals&bookingId={booking_id}"
    )


def calendar_portal_route(branch_code: str, booking_id: str) -> str:
    return (
        f"{_APP_BASE}/{_branch_path_suffix(branch_code)}"
        f"?bookingId={booking_id}"
    )


def _post_notification(payload: dict[str, Any]) -> bool:
    if not scheduling_portal_notifications_enabled():
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN

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
            "scheduling_portal_notification_rejected status=%s event=%s",
            response.status_code,
            (payload.get("metadata") or {}).get("event"),
        )
    except Exception:
        logger.warning(
            "scheduling_portal_notification_failed event=%s",
            (payload.get("metadata") or {}).get("event"),
            exc_info=True,
        )
    return False


def notify_booking_approval_requested(
    *,
    booking: dict[str, Any],
) -> bool:
    booking_id = str(booking.get("id") or "")
    branch = str(booking.get("branch_code") or "")
    approve_perm = SCHEDULING_BRANCH_APPROVE_PERMS.get(branch)
    if not booking_id or not approve_perm:
        return False

    title = str(booking.get("title") or "Reserva")
    resource_name = str(booking.get("resource_name") or "recurso")
    requester = str(booking.get("booked_by_name") or "Usuário")
    requester_id = str(booking.get("booked_by_user_id") or "").strip()

    payload: dict[str, Any] = {
        "permissionCodes": [approve_perm],
        "excludedUserIds": [requester_id] if requester_id and requester_id != "unknown" else [],
        "title": "Agendamento aguardando aprovação",
        "message": (
            f"{requester} solicitou «{title}» em {resource_name}. "
            "Abra a fila de aprovações para confirmar ou rejeitar."
        ),
        "type": "warning",
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": "Abrir aprovações",
            "target": approvals_portal_route(branch, booking_id),
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": "booking_approval_requested",
            "dedupeKey": f"scheduling:approval-requested:{booking_id}",
            "bookingId": booking_id,
            "branchCode": branch,
            "deepPath": f"?tab=approvals&bookingId={booking_id}",
        },
    }
    return _post_notification(payload)


def notify_booking_decision(
    *,
    booking: dict[str, Any],
    event_type: str,
) -> bool:
    booking_id = str(booking.get("id") or "")
    branch = str(booking.get("branch_code") or "")
    recipient = str(booking.get("booked_by_user_id") or "").strip()
    if not booking_id or not recipient or recipient == "unknown":
        return False

    title = str(booking.get("title") or "Reserva")
    decided_by = str(booking.get("decided_by_name") or "Sistema")
    reason = (booking.get("decision_reason") or "").strip()

    if event_type == "booking_approved":
        notif_type = "success"
        notif_title = "Agendamento confirmado"
        message = f"Sua reserva «{title}» foi confirmada por {decided_by}."
    elif event_type == "booking_rejected":
        notif_type = "error"
        notif_title = "Agendamento rejeitado"
        message = f"Sua reserva «{title}» foi rejeitada por {decided_by}."
        if reason:
            message = f"{message} Motivo: {reason}"
    elif event_type == "booking_expired":
        notif_type = "warning"
        notif_title = "Agendamento expirado"
        message = (
            f"Sua solicitação «{title}» expirou sem aprovação no prazo. "
            "O horário foi liberado."
        )
    else:
        return False

    payload: dict[str, Any] = {
        "userIds": [recipient],
        "title": notif_title,
        "message": message,
        "type": notif_type,
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": "Ver agendamento",
            "target": calendar_portal_route(branch, booking_id),
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": event_type,
            "dedupeKey": f"scheduling:{event_type}:{booking_id}",
            "bookingId": booking_id,
            "branchCode": branch,
            "decidedByName": decided_by,
            "decisionReason": reason or None,
        },
    }
    return _post_notification(payload)
