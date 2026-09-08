from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests

from app.domain.exceptions import CoreApiUnavailableError
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("supplies-api.core_api")


class CoreApiHttpGateway:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or Settings.CORE_API_BASE_URL).rstrip("/") + "/"
        self.timeout = timeout_seconds if timeout_seconds is not None else Settings.CORE_API_TIMEOUT_SECONDS

    def get_me(self, access_token: str) -> dict:
        url = urljoin(self.base_url, "me")
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.exception("core_api_request_failed path=me")
            raise CoreApiUnavailableError("Core API request failed") from exc

        if response.status_code >= 500:
            raise CoreApiUnavailableError("Core API server error")

        if response.status_code in (401, 403):
            raise CoreApiUnavailableError("Core API refused authorization lookup")

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CoreApiUnavailableError("Invalid Core API response") from exc

        if not isinstance(data, dict):
            raise CoreApiUnavailableError("Invalid Core API response")

        return data

    def lookup_directory_users(
        self,
        *,
        access_token: str,
        user_ids: list[str],
    ) -> dict[str, dict[str, str]]:
        """Best-effort directory lookup with the caller's Bearer (admin reading others)."""
        ordered: list[str] = []
        seen: set[str] = set()
        for raw in user_ids:
            user_id = str(raw or "").strip()
            if not user_id or user_id in seen:
                continue
            seen.add(user_id)
            ordered.append(user_id)
        if not ordered:
            return {}

        url = urljoin(self.base_url, "integrations/directory/users/lookup")
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"ids": ordered},
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception("core_api_directory_lookup_failed")
            return {}

        if response.status_code >= 400:
            return {}

        try:
            payload = response.json()
        except ValueError:
            return {}

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}

        result: dict[str, dict[str, str]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            user_id = str(item.get("id") or "").strip()
            if not user_id:
                continue
            name = str(item.get("name") or item.get("display_name") or "").strip()
            email = str(item.get("email") or "").strip()
            result[user_id] = {
                "id": user_id,
                "name": name or user_id,
                "email": email,
            }
        return result
