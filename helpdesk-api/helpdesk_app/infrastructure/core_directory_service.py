"""Gateway Core — directory Minha DELPI (S2S) para enriquecer o catálogo do helpdesk."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from helpdesk_app.config import settings

logger = logging.getLogger("helpdesk.directory")


class CoreDirectoryService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        app_id: str = "helpdesk",
        connect_timeout: float = 3.0,
        read_timeout: float = 8.0,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.app_id = app_id
        self._timeout = httpx.Timeout(read_timeout, connect=connect_timeout)

    def configured(self) -> bool:
        return bool(self.core_api_url and self.service_token)

    def search_users(
        self,
        *,
        q: str = "",
        limit: int = 20,
        browse: bool = False,
        permission: str | None = None,
    ) -> list[dict[str, str]]:
        """Returns [{id, name, email}] from Minha DELPI directory (unmasked email)."""
        if not self.configured():
            return []

        safe_limit = max(1, min(int(limit or 20), 50))
        params: dict[str, str] = {
            "limit": str(safe_limit),
            "app": self.app_id,
        }
        permission_code = (permission or "").strip()
        if permission_code:
            params["permission"] = permission_code
        term = (q or "").strip()
        if term:
            params["q"] = term
        elif browse:
            params["browse"] = "true"
        else:
            return []

        headers = {
            "Authorization": f"Bearer {self.service_token}",
            "X-Delpi-Service-Token": self.service_token,
            "Accept": "application/json",
        }
        try:
            response = httpx.get(
                f"{self.core_api_url}/integrations/directory/users",
                headers=headers,
                params=params,
                timeout=self._timeout,
            )
        except Exception:
            logger.exception("helpdesk_directory_search_failed")
            return []

        if response.status_code >= 400:
            logger.warning(
                "helpdesk_directory_search_rejected status=%s body=%s",
                response.status_code,
                response.text[:300],
            )
            return []

        try:
            payload: Any = response.json()
        except ValueError:
            logger.warning("helpdesk_directory_search_invalid_json")
            return []

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []

        out: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("id") or "").strip()
            name = str(item.get("name") or "").strip()
            email = str(item.get("email") or "").strip().lower()
            if not user_id or "@" not in email:
                continue
            out.append({"id": user_id, "name": name or email, "email": email})
        return out
