from __future__ import annotations

import logging
from typing import Any

import httpx

from cipa_app.config import settings

logger = logging.getLogger("cipa.notifications")


class CipaPortalNotificationService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = service_token if service_token is not None else settings.CORE_API_SERVICE_TOKEN
        self.enabled = (
            settings.CIPA_PORTAL_NOTIFICATIONS_ENABLED if enabled is None else enabled
        )

    def send(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        portal_route: str | None = None,
    ) -> bool:
        if not self.enabled:
            return False
        if not self.service_token:
            logger.warning("cipa_notification_skipped_no_token")
            return False
        payload: dict[str, Any] = {
            "userId": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
        }
        if portal_route:
            payload["portalRoute"] = portal_route
        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10.0,
            )
            if response.status_code >= 400:
                logger.warning(
                    "cipa_notification_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                return False
            return True
        except Exception:
            logger.exception("cipa_notification_failed user=%s", user_id)
            return False
