"""Gateway S2S — lookup de acesso ao Portal Comercial via core-api directory."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import httpx

from commercial_app.config import settings
from commercial_app.domain.ports.portal_access_port import PortalAccessPort

logger = logging.getLogger("commercial.portal_access")

_COMMERCIAL_APP_ID = "commercial"
_LOOKUP_CHUNK_SIZE = 50


class CoreApiPortalAccessPort(PortalAccessPort):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        service_token: str | None = None,
        timeout: float | None = None,
        app_id: str = _COMMERCIAL_APP_ID,
    ) -> None:
        self._base_url = (base_url or settings.CORE_API_BASE_URL or "").rstrip("/")
        self._service_token = (
            service_token
            if service_token is not None
            else (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "")
        ).strip()
        self._timeout = float(timeout if timeout is not None else settings.CORE_API_TIMEOUT)
        self._app_id = (app_id or _COMMERCIAL_APP_ID).strip() or _COMMERCIAL_APP_ID

    def configured(self) -> bool:
        return bool(self._base_url and self._service_token)

    def has_commercial_portal_access_batch(
        self,
        user_ids: Sequence[str],
    ) -> dict[str, bool]:
        ids = [
            str(item or "").strip()
            for item in user_ids
            if str(item or "").strip()
        ]
        # Dedup estável.
        ordered: list[str] = []
        seen: set[str] = set()
        for user_id in ids:
            if user_id in seen:
                continue
            seen.add(user_id)
            ordered.append(user_id)

        result = {user_id: False for user_id in ordered}
        if not ordered:
            return result
        if not self.configured():
            logger.warning("core_api_portal_access_not_configured")
            return result

        headers = {
            "Authorization": f"Bearer {self._service_token}",
            "X-Delpi-Service-Token": self._service_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        for offset in range(0, len(ordered), _LOOKUP_CHUNK_SIZE):
            chunk = ordered[offset : offset + _LOOKUP_CHUNK_SIZE]
            try:
                response = httpx.post(
                    f"{self._base_url}/integrations/directory/users/lookup",
                    headers=headers,
                    json={"ids": chunk, "app": self._app_id},
                    timeout=self._timeout,
                )
            except Exception:
                logger.exception("core_api_portal_access_lookup_failed")
                continue

            if response.status_code >= 400:
                logger.warning(
                    "core_api_portal_access_lookup_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                continue

            try:
                payload: Any = response.json()
            except ValueError:
                logger.warning("core_api_portal_access_lookup_invalid_json")
                continue

            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                user_id = str(item.get("id") or "").strip()
                if not user_id or user_id not in result:
                    continue
                if "has_app_access" in item:
                    result[user_id] = bool(item.get("has_app_access"))
                else:
                    # Lookup sem flag (legado) = ativo encontrado → acesso.
                    result[user_id] = True

        return result
