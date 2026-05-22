from __future__ import annotations

import logging
from typing import Any

import requests

from tm_app.config import settings

logger = logging.getLogger(__name__)


class CoreNotificationsClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        enabled: bool | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._enabled = settings.TM_NOTIFICATIONS_ENABLED if enabled is None else enabled
        self._base_url = (base_url or settings.TM_CORE_API_URL or "").rstrip("/")
        self._token = (service_token or settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        self._timeout = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self._enabled and self._base_url and self._token)

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.is_configured:
            logger.debug("core_notifications_skipped not_configured")
            return None

        url = f"{self._base_url}/integrations/notifications"
        headers = {
            "Content-Type": "application/json",
            "X-Delpi-Service-Token": self._token,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()
        except requests.RequestException as exc:
            logger.warning("core_notifications_dispatch_failed err=%s", exc)
            return None
