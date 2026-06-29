"""Proxy core-api para usuários atribuíveis em planos PAC."""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PAC_QUALITY_APP_ID = "quality-action-plans"


class CoreApiDirectoryService:
    def configured(self) -> bool:
        return bool(
            (settings.CORE_API_BASE_URL or "").strip()
            and (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        )

    def search_assignable_users(
        self,
        *,
        query: str | None,
        limit: int = 10,
        browse: bool = False,
    ) -> list[dict]:
        if not self.configured():
            return []

        base_url = (settings.CORE_API_BASE_URL or "").rstrip("/")
        token = (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
        normalized = (query or "").strip()
        params: dict[str, str | int] = {
            "limit": max(1, min(limit, 20)),
            "app": _PAC_QUALITY_APP_ID,
        }
        if normalized:
            params["q"] = normalized
        if browse or not normalized:
            params["browse"] = "true"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Delpi-Service-Token": token,
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{base_url}/integrations/directory/users",
                    params=params,
                    headers=headers,
                )
            if response.status_code >= 400:
                logger.warning(
                    "core_api_directory_search_failed status=%s",
                    response.status_code,
                )
                return []
            payload = response.json()
            items = payload.get("items") if isinstance(payload, dict) else None
            return items if isinstance(items, list) else []
        except Exception:
            logger.exception("core_api_directory_search_error")
            return []
