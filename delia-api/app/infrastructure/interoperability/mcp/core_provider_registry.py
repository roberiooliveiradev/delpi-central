"""HTTP client for Core MCP provider eligibility (S2S).

Fail closed: transport/auth/parse errors raise; callers must not fall
back to hardcoded specialist enablement.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

logger = logging.getLogger(__name__)


class CoreMcpProviderRegistryError(RuntimeError):
    """Core MCP provider registry unavailable or unauthorized."""


class CoreMcpProviderRegistryClient:
    """GET /integrations/mcp-providers/eligible via integrations service token."""

    def __init__(
        self,
        *,
        core_api_url: str,
        service_token: str,
        timeout_seconds: float,
        http_get: Callable[..., Any],
    ) -> None:
        self._base = (core_api_url or "").rstrip("/")
        self._token = (service_token or "").strip()
        self._timeout = float(timeout_seconds)
        self._http_get = http_get

    def list_eligible(self) -> list[Mapping[str, Any]]:
        if not self._base:
            raise CoreMcpProviderRegistryError("core_api_url_missing")
        if not self._token:
            raise CoreMcpProviderRegistryError("integrations_token_missing")
        url = f"{self._base}/integrations/mcp-providers/eligible"
        try:
            response = self._http_get(
                url,
                headers={
                    "X-Delpi-Service-Token": self._token,
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        except Exception as exc:
            raise CoreMcpProviderRegistryError("core_unavailable") from exc

        status = getattr(response, "status_code", None)
        if status in {401, 403}:
            raise CoreMcpProviderRegistryError("core_forbidden")
        if status != 200:
            raise CoreMcpProviderRegistryError(f"core_http_{status}")

        try:
            payload = response.json()
        except Exception as exc:
            raise CoreMcpProviderRegistryError("core_malformed_response") from exc

        if not isinstance(payload, dict):
            raise CoreMcpProviderRegistryError("core_malformed_response")
        items = payload.get("items")
        if not isinstance(items, list):
            raise CoreMcpProviderRegistryError("core_malformed_response")
        return [i for i in items if isinstance(i, Mapping)]
