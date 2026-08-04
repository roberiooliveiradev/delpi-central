"""Cliente HTTP do BFF TV Dashboard (copiloto → preview/apply patch)."""

from __future__ import annotations

from typing import Any

import requests

from app.infrastructure.config.settings import Settings


class TvDashboardApiGateway:
    def __init__(self, *, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or Settings.TV_DASHBOARD_API_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else Settings.TV_DASHBOARD_API_TIMEOUT_SECONDS

    def get_capabilities(self, access_token: str) -> dict[str, Any]:
        """GET /data/copilot/capabilities — catálogo versionado (sem ops embutidas na AI)."""
        return self._get("/data/copilot/capabilities", access_token=access_token)

    def suggest_ops(
        self,
        *,
        message: str,
        host_context: dict[str, Any] | None,
        access_token: str,
    ) -> dict[str, Any]:
        """POST /data/copilot/suggest-ops — NL + host → ops tipadas no BFF."""
        return self._post(
            "/data/copilot/suggest-ops",
            {
                "message": str(message or ""),
                "hostContext": host_context if isinstance(host_context, dict) else {},
            },
            access_token=access_token,
        )

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

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        bearer = (
            access_token
            if access_token.startswith("Bearer ")
            else f"Bearer {access_token}"
        )
        return {
            "Authorization": bearer,
            "Accept": "application/json",
        }

    def _get(self, path: str, *, access_token: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.get(
            url,
            headers=self._auth_headers(access_token),
            timeout=self.timeout,
        )
        return self._normalize_response(response)

    def _post(self, path: str, body: dict[str, Any], *, access_token: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            **self._auth_headers(access_token),
            "Content-Type": "application/json",
        }
        response = requests.post(url, json=body, headers=headers, timeout=self.timeout)
        return self._normalize_response(response)

    @staticmethod
    def _normalize_response(response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        if not isinstance(payload, dict):
            payload = {"data": payload}
        payload.setdefault("_httpStatus", response.status_code)
        payload.setdefault("_ok", response.ok)
        return payload
