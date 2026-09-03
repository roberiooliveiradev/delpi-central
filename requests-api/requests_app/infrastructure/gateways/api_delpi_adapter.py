from __future__ import annotations

from typing import Any

import httpx

from requests_app.config import settings
from requests_app.domain.entities import Request
from requests_app.domain.ports.request_destination_port import (
    DeliveryResult,
    RequestDestinationPort,
)


class ApiDelpiAdapter(RequestDestinationPort):
    """Stub destination for TOTVS lookups via api-delpi (real lookups = E6)."""

    adapter_name = "api_delpi"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.DELPI_API_URL).rstrip("/")
        self._timeout = timeout or float(settings.DELPI_API_TIMEOUT or 30)
        self._caller_app = (caller_app or settings.DELPI_API_CALLER_APP or "requests-api").strip()

    def health(self) -> DeliveryResult:
        headers = {"X-Delpi-Caller-App": self._caller_app}
        try:
            with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
                response = client.get("/health", headers=headers)
            if response.status_code >= 400:
                return DeliveryResult(
                    ok=False,
                    detail=f"api-delpi health HTTP {response.status_code}",
                    meta={"status_code": response.status_code},
                )
            return DeliveryResult(
                ok=True,
                detail="api-delpi reachable",
                meta={"status_code": response.status_code},
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(ok=False, detail=str(exc))

    def deliver(
        self,
        *,
        request: Request,
        event_type: str,
        payload: dict[str, Any],
    ) -> DeliveryResult:
        return DeliveryResult(
            ok=True,
            detail="api_delpi deliver stub (lookups deferred to E6)",
            meta={
                "request_id": str(request.id),
                "event_type": event_type,
                "payload_keys": sorted(payload.keys()),
            },
        )
