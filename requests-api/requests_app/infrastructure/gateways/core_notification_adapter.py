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
) -> dict[str, Any]:
    title_map = {
        "request.created": "Nova solicitação",
        "request.transition": "Solicitação atualizada",
    }
    return {
        "category": "my_requests",
        "sourceApp": "my-requests",
        "title": title_map.get(event_type, "Minhas Solicitações"),
        "body": f"{request_number} ({type_code}) — {status} por {actor_name}",
        "link": f"/apps/my-requests/requests/{request_id}",
        "dedupeKey": f"my-requests:{event_type}:{request_id}:{status}",
        "meta": {
            "requestId": request_id,
            "requestNumber": request_number,
            "typeCode": type_code,
            "status": status,
            "eventType": event_type,
        },
    }
