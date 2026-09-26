from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from delpi_auth.service_token import apply_internal_service_headers

from production_control_app.config import settings
from production_control_app.domain.errors import PulseGatewayError


class ProductionPulseGateway:
    """Cliente S2S → production-pulse-api (snapshot de contador)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        caller_app: str = "production-control-api",
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.PRODUCTION_PULSE_API_URL).rstrip("/")
        self._timeout = (
            timeout if timeout is not None else float(settings.PRODUCTION_PULSE_API_TIMEOUT)
        )
        self._caller_app = caller_app
        self._client = client or httpx.Client(timeout=self._timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-Delpi-Caller-App": self._caller_app,
        }
        apply_internal_service_headers(headers)
        return headers

    def _unwrap(self, body: Any) -> Any:
        if isinstance(body, dict) and "data" in body:
            return body.get("data")
        return body

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = self._client.request(
                method,
                url,
                headers=self._headers(),
                params=params,
            )
        except httpx.HTTPError as exc:
            raise PulseGatewayError(f"Falha de rede ao consultar o Pulso: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text[:240]
            raise PulseGatewayError(
                f"Pulso retornou HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise PulseGatewayError("Resposta inválida do Pulso (JSON).") from exc
        return self._unwrap(payload)

    def fetch_work_center_snapshot(
        self,
        *,
        branch: str,
        work_center: str,
        role_key: str = "pulse_counter",
    ) -> dict[str, Any]:
        data = self._request(
            "GET",
            "/integrations/devices/snapshot",
            params={
                "branch": branch,
                "workCenter": work_center,
                "roleKey": role_key,
            },
        )
        return data if isinstance(data, dict) else {"items": []}

    def fetch_device_snapshot(self, device_id: str) -> dict[str, Any]:
        data = self._request(
            "GET",
            f"/integrations/devices/{quote(str(device_id), safe='')}/snapshot",
        )
        return data if isinstance(data, dict) else {}
