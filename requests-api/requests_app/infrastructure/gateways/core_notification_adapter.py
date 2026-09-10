from __future__ import annotations

import logging
from typing import Any, Protocol

import httpx

from delpi_auth.service_token import apply_internal_service_headers
from requests_app.config import settings
from requests_app.domain.ports.integration_outbox_port import IntegrationOutboxRow

logger = logging.getLogger(__name__)


class PortalNotificationPort(Protocol):
    def publish(self, row: IntegrationOutboxRow) -> None: ...


class CoreNotificationAdapter:
    """POST /core-api/integrations/notifications via S2S token."""

    def __init__(self, *, base_url: str | None = None, timeout: float = 10.0) -> None:
        self.base_url = (base_url or settings.CORE_API_URL).rstrip("/")
        self.timeout = timeout

    def publish(self, row: IntegrationOutboxRow) -> None:
        payload = dict(row.payload or {})
        headers = {"Content-Type": "application/json", "X-Delpi-Caller-App": "requests-api"}
        apply_internal_service_headers(headers)
        url = f"{self.base_url}/integrations/notifications"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()


class InMemoryPortalNotificationAdapter:
    def __init__(self) -> None:
        self.published: list[IntegrationOutboxRow] = []

    def publish(self, row: IntegrationOutboxRow) -> None:
        self.published.append(row)


def build_notification_payload(
    *,
    event_type: str,
    request_id: str,
    request_number: str,
    type_code: str,
    status: str,
    actor_name: str,
    recipient_user_ids: list[str] | None = None,
    title: str | None = None,
    message: str | None = None,
    notification_type: str = "info",
) -> dict[str, Any]:
    """Core-compatible payload for POST /integrations/notifications."""
    default_titles = {
        "request.created": "Nova solicitação",
        "request.transition": "Solicitação atualizada",
    }
    resolved_title = (title or "").strip() or default_titles.get(
        event_type, "Minhas Solicitações"
    )
    resolved_message = (message or "").strip() or (
        f"{request_number} ({type_code}) — {status} por {actor_name}"
    )
    link = f"/apps/my-requests/requests/{request_id}"
    payload: dict[str, Any] = {
        "category": "my_requests",
        "sourceApp": "my-requests",
        "title": resolved_title,
        "message": resolved_message,
        "type": notification_type if notification_type in {"info", "success", "warning", "error"} else "info",
        "action": {
            "type": "portal_route",
            "label": "Abrir solicitação",
            "target": link,
        },
        "metadata": {
            "source": "my-requests",
            "event": event_type,
            "dedupeKey": f"my-requests:{event_type}:{request_id}:{status}",
            "requestId": request_id,
            "requestNumber": request_number,
            "typeCode": type_code,
            "status": status,
            "eventType": event_type,
        },
    }
    recipients = [
        str(uid).strip() for uid in (recipient_user_ids or []) if str(uid).strip()
    ]
    if recipients:
        payload["userIds"] = recipients
    return payload
