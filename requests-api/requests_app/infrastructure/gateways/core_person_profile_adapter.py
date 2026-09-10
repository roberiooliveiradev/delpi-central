"""Core person-profile S2S gateway — avatar ownership stays in core-api."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from requests_app.config import settings

logger = logging.getLogger(__name__)


def _core_integrations_token() -> str:
    """Core S2S expects CORE_API_INTEGRATIONS_SERVICE_TOKEN (not API_DELPI_*)."""
    return (
        os.getenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN")
        or os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN")
        or ""
    ).strip()


class CorePersonProfileAdapter:
    """GET /integrations/person-profiles/{user_id}/photo via S2S token."""

    def __init__(self, *, base_url: str | None = None, timeout: float = 8.0) -> None:
        self.base_url = (base_url or settings.CORE_API_URL).rstrip("/")
        self.timeout = timeout

    def configured(self) -> bool:
        return bool(self.base_url) and bool(_core_integrations_token())

    def _headers(self, *, accept: str = "application/json") -> dict[str, str]:
        token = _core_integrations_token()
        headers = {
            "Accept": accept,
            "X-Delpi-Caller-App": "requests-api",
        }
        if token:
            headers["X-Delpi-Service-Token"] = token
            headers["Authorization"] = (
                token if token.startswith("Bearer ") else f"Bearer {token}"
            )
        return headers

    def get_photo(
        self, user_id: str
    ) -> tuple[bytes, str, str] | None:
        """Returns (content, content_type, file_name) or None when missing/unavailable."""
        uid = (user_id or "").strip()
        if not uid or not self.configured():
            return None
        try:
            response = httpx.get(
                f"{self.base_url}/integrations/person-profiles/{uid}/photo",
                headers=self._headers(accept="*/*"),
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("core_person_profile_photo_failed user_id=%s", uid)
            return None
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            logger.warning(
                "core_person_profile_photo_rejected status=%s user_id=%s",
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

    def lookup_has_photo(self, user_ids: list[str]) -> dict[str, bool]:
        """Batch metadata: user_id → has_photo. Best-effort; empty on failure."""
        ids = [str(uid).strip() for uid in user_ids if str(uid).strip()]
        if not ids or not self.configured():
            return {}
        try:
            response = httpx.post(
                f"{self.base_url}/integrations/person-profiles/lookup",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"ids": ids[:50]},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except Exception:
            logger.exception("core_person_profile_lookup_failed")
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


class InMemoryCorePersonProfileAdapter:
    def __init__(self) -> None:
        self.photos: dict[str, tuple[bytes, str, str]] = {}
        self.has_photo: dict[str, bool] = {}

    def configured(self) -> bool:
        return True

    def get_photo(self, user_id: str) -> tuple[bytes, str, str] | None:
        return self.photos.get((user_id or "").strip())

    def lookup_has_photo(self, user_ids: list[str]) -> dict[str, bool]:
        return {
            uid: self.has_photo.get(uid, False)
            for uid in ((u or "").strip() for u in user_ids)
            if uid
        }
