from __future__ import annotations

import logging
from typing import Any

import httpx

from tm_app.config import settings

logger = logging.getLogger("transformometro.atas.notifications")


class TmPortalNotificationService:
    def __init__(
        self, *, core_api_url: str | None = None, service_token: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_BASE_URL).rstrip("/")
        self.service_token = service_token if service_token is not None else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        self.enabled = settings.TM_PORTAL_NOTIFICATIONS_ENABLED if enabled is None else enabled

    def send(
        self, *, user_id: str, title: str, message: str, notification_type: str = "info",
        portal_route: str | None = None,
    ) -> bool:
        if not self.enabled or not self.service_token:
            return False
        payload: dict[str, Any] = {"userId": user_id, "title": title, "message": message, "type": notification_type}
        if portal_route:
            payload["portalRoute"] = portal_route
        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/notifications",
                headers={"Authorization": f"Bearer {self.service_token}", "Content-Type": "application/json"},
                json=payload, timeout=10.0,
            )
            if response.status_code >= 400:
                logger.warning("tm_ata_notification_rejected status=%s", response.status_code)
                return False
            return True
        except Exception:
            logger.exception("tm_ata_notification_failed user=%s", user_id)
            return False
