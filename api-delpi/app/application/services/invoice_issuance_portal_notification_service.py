"""Notificações in-app — solicitação de emissão de NF via Core API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.application.security.api_delpi_permissions import INVOICE_ISSUANCE_PROCESS
from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "invoice-issuance"
_CATEGORY = "invoice_issuance"
_APP_BASE = "/apps/my-requests"


def invoice_issuance_notifications_enabled() -> bool:
    if not settings.INVOICE_ISSUANCE_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def request_portal_route(*, branch_code: str | None, request_id: str) -> str:
    """Deep link canônico (E13): detalhe em my-requests (mesmo UUID pós-migração)."""
    _ = branch_code
    return f"{_APP_BASE}/requests/{request_id}"


def _post_notification(payload: dict[str, Any]) -> bool:
    if not invoice_issuance_notifications_enabled():
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
            "invoice_issuance_notification_rejected status=%s event=%s",
            response.status_code,
            (payload.get("metadata") or {}).get("event"),
        )
    except Exception:
        logger.warning(
            "invoice_issuance_notification_failed event=%s",
            (payload.get("metadata") or {}).get("event"),
            exc_info=True,
        )
    return False


def _party_label(request: dict[str, Any]) -> str:
    return str(request.get("party_name") or "destinatário")


def notify_request_created(request: dict[str, Any], *, actor_user_id: str | None) -> bool:
    request_id = str(request.get("id") or "")
    if not request_id:
        return False
    requester = str(request.get("created_by_name") or "Alguém")
    excluded = [actor_user_id] if actor_user_id and actor_user_id != "unknown" else []
    return _post_notification(
        {
            "permissionCodes": [INVOICE_ISSUANCE_PROCESS],
            "excludedUserIds": excluded,
            "title": "Nova solicitação de emissão de NF",
            "message": (
                f"{requester} cadastrou uma solicitação para {_party_label(request)}. "
                "Abra a fila do Faturamento para atender."
            ),
            "type": "warning",
            "category": _CATEGORY,
            "sourceApp": _SOURCE_APP,
            "action": {
                "type": "portal_route",
                "label": "Abrir solicitação",
                "target": request_portal_route(
                    branch_code=str(request.get("branch_code") or ""),
                    request_id=request_id,
                ),
            },
            "metadata": {
                "source": _SOURCE_APP,
                "event": "invoice_issuance_created",
                "dedupeKey": f"invoice-issuance:created:{request_id}:{request.get('updated_at')}",
                "requestId": request_id,
                "branchCode": request.get("branch_code"),
            },
        }
    )


def _notify_requester(
    request: dict[str, Any],
    *,
    actor_user_id: str | None,
    title: str,
    message: str,
    event: str,
    ntype: str = "info",
) -> bool:
    request_id = str(request.get("id") or "")
    requester_id = str(request.get("created_by_user_id") or "").strip()
    if not request_id or not requester_id or requester_id == "unknown":
        return False
    if actor_user_id and actor_user_id == requester_id:
        return False
    return _post_notification(
        {
            "userIds": [requester_id],
            "title": title,
            "message": message,
            "type": ntype,
            "category": _CATEGORY,
            "sourceApp": _SOURCE_APP,
            "action": {
                "type": "portal_route",
                "label": "Abrir solicitação",
                "target": request_portal_route(
                    branch_code=str(request.get("branch_code") or ""),
                    request_id=request_id,
                ),
            },
            "metadata": {
                "source": _SOURCE_APP,
                "event": event,
                "dedupeKey": f"invoice-issuance:{event}:{request_id}",
                "requestId": request_id,
                "branchCode": request.get("branch_code"),
            },
        }
    )


def notify_request_returned(request: dict[str, Any], *, actor_user_id: str | None) -> bool:
    reason = str(request.get("return_reason") or "ajuste de informações")
    return _notify_requester(
        request,
        actor_user_id=actor_user_id,
        title="Solicitação de NF devolvida",
        message=f"O Faturamento devolveu a solicitação para {_party_label(request)}: {reason}",
        event="invoice_issuance_returned",
        ntype="warning",
    )


def notify_request_issued(request: dict[str, Any], *, actor_user_id: str | None) -> bool:
    return _notify_requester(
        request,
        actor_user_id=actor_user_id,
        title="Nota fiscal marcada como emitida",
        message=f"A solicitação para {_party_label(request)} foi marcada como emitida.",
        event="invoice_issuance_issued",
    )


def notify_request_cancelled(request: dict[str, Any], *, actor_user_id: str | None) -> bool:
    return _notify_requester(
        request,
        actor_user_id=actor_user_id,
        title="Solicitação de NF cancelada",
        message=f"A solicitação para {_party_label(request)} foi cancelada.",
        event="invoice_issuance_cancelled",
        ntype="warning",
    )
