"""Gateway Core — resolve e-mails por user id (S2S)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from cipa_app.config import settings

logger = logging.getLogger("cipa.directory")


class CipaCoreDirectoryService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_SERVICE_TOKEN
        )

    def configured(self) -> bool:
        return bool(self.core_api_url and self.service_token)

    def lookup_emails_by_user_ids(self, user_ids: list[str]) -> dict[str, str]:
        ids = [str(item or "").strip() for item in user_ids if str(item or "").strip()]
        if not ids or not self.configured():
            return {}

        headers = {
            "Authorization": f"Bearer {self.service_token}",
            "X-Delpi-Service-Token": self.service_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/directory/users/lookup",
                headers=headers,
                json={"ids": ids},
                timeout=10.0,
            )
        except Exception:
            logger.exception("cipa_directory_lookup_failed")
            return {}

        if response.status_code >= 400:
            logger.warning(
                "cipa_directory_lookup_rejected status=%s body=%s",
                response.status_code,
                response.text[:300],
            )
            return {}

        try:
            payload: Any = response.json()
        except ValueError:
            logger.warning("cipa_directory_lookup_invalid_json")
            return {}

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}

        result: dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("id") or "").strip()
            email = str(item.get("email") or "").strip()
            if not user_id or "@" not in email:
                continue
            result[user_id] = email
        return result
