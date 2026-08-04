"""Cliente HTTP do BFF TV Dashboard (copiloto → preview/apply patch)."""

from __future__ import annotations

from typing import Any

import requests

from app.infrastructure.config.settings import Settings


class TvDashboardApiGateway:
    def __init__(self, *, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or Settings.TV_DASHBOARD_API_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else Settings.TV_DASHBOARD_API_TIMEOUT_SECONDS

    def preview_patch(
        self,
        envelope: dict[str, Any],
        *,
        access_token: str,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        return self._post(
            "/data/copilot/preview-patch",
            {
                "target": envelope.get("target") or {},
                "ops": envelope.get("ops") or [],
                "includeFingerprint": include_fingerprint,
            },
            access_token=access_token,
        )

    def apply_patch(
        self,
        envelope: dict[str, Any],
        *,
        access_token: str,
    ) -> dict[str, Any]:
        return self._post(
            "/data/copilot/apply-patch",
            {
                "target": envelope.get("target") or {},
                "ops": envelope.get("ops") or [],
            },
            access_token=access_token,
        )

    def _post(self, path: str, body: dict[str, Any], *, access_token: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {access_token}" if not access_token.startswith("Bearer ") else access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(url, json=body, headers=headers, timeout=self.timeout)
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        if not isinstance(payload, dict):
            payload = {"data": payload}
        payload.setdefault("_httpStatus", response.status_code)
        payload.setdefault("_ok", response.ok)
        return payload
