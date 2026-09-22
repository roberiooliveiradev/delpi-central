"""Gateway Core S2S — person-profile has_photo + photo bytes (avatar Minha DELPI)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from helpdesk_app.config import settings

logger = logging.getLogger("helpdesk.person_profile")

_LOOKUP_MAX_IDS = 50


class CorePersonProfileService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.timeout = timeout

    def configured(self) -> bool:
        return bool(self.core_api_url and self.service_token)

    def _headers(self, *, accept: str = "application/json") -> dict[str, str]:
        token = (self.service_token or "").strip()
        headers = {
            "Accept": accept,
            "X-Delpi-Caller-App": "helpdesk",
        }
        if token:
            headers["X-Delpi-Service-Token"] = token
            headers["Authorization"] = (
                token if token.startswith("Bearer ") else f"Bearer {token}"
            )
        return headers

    def lookup_has_photo(self, user_ids: list[str]) -> dict[str, bool]:
        """Batch metadata: directory user_id → has_photo. Soft-fail empty."""
        ids = [str(uid).strip() for uid in user_ids if str(uid).strip()][:_LOOKUP_MAX_IDS]
        if not ids or not self.configured():
            return {}
        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/person-profiles/lookup",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"ids": ids},
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("helpdesk_person_profile_lookup_failed")
            return {}

        if response.status_code >= 400:
            logger.warning(
                "helpdesk_person_profile_lookup_rejected status=%s body=%s",
                response.status_code,
                response.text[:300],
            )
            return {}

        try:
            payload: Any = response.json()
        except ValueError:
            logger.warning("helpdesk_person_profile_lookup_invalid_json")
            return {}

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}

        out: dict[str, bool] = {}
        for row in items:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("user_id") or "").strip()
            if uid:
                out[uid] = bool(row.get("has_photo"))
        return out

    def get_photo_bytes(self, user_id: str) -> tuple[bytes, str, str] | None:
        """Returns (content, content_type, file_name) or None when missing."""
        uid = (user_id or "").strip()
        if not uid or not self.configured():
            return None
        try:
            response = httpx.get(
                f"{self.core_api_url}/integrations/person-profiles/{uid}/photo",
                headers=self._headers(accept="*/*"),
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("helpdesk_person_profile_photo_failed user_id=%s", uid)
            return None

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.warning(
                "helpdesk_person_profile_photo_rejected status=%s user_id=%s",
                response.status_code,
                uid,
            )
            return None

        content_type = (
            response.headers.get("content-type") or "application/octet-stream"
        ).split(";")[0].strip()
        file_name = "photo.bin"
        disposition = response.headers.get("content-disposition") or ""
        if "filename=" in disposition:
            file_name = (
                disposition.split("filename=", 1)[1].strip().strip('"') or file_name
            )
        return response.content, content_type, file_name
