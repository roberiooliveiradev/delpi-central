from __future__ import annotations

from typing import Any

import httpx

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.domain.models.device_reading import CommandResult, DeviceReading
from production_pulse_app.infrastructure.drivers.device_http_support import (
    device_base_url,
    parse_gauge_response,
)

_DRIVER_KEY = "esp8266_gauge_v1"
_READ_PATH = "/api/sensores"


class Esp8266GaugeDriver:
    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    @property
    def driver_key(self) -> str:
        return _DRIVER_KEY

    def _timeout_for(self, device: dict[str, Any]) -> float:
        if self._timeout_seconds is not None:
            return self._timeout_seconds
        driver_key = str(device.get("driver_key") or device.get("driverKey") or _DRIVER_KEY)
        timeout_ms = get_device_driver_registry().poll_timeout_ms(driver_key)
        return max(0.5, timeout_ms / 1000.0)

    def capabilities(self) -> frozenset[str]:
        return frozenset()

    def read(self, device: dict[str, Any]) -> DeviceReading:
        return self._fetch_gauge(device)

    def test(self, device: dict[str, Any]) -> DeviceReading:
        return self.read(device)

    def execute(
        self,
        device: dict[str, Any],
        command_key: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> CommandResult:
        _ = device, payload
        normalized = (command_key or "").strip().lower()
        if not normalized:
            return CommandResult(success=False, error_message="Comando não suportado.")
        return CommandResult(
            success=False,
            error_message=f"Comando não suportado: {command_key}",
        )

    def _fetch_gauge(self, device: dict[str, Any]) -> DeviceReading:
        body = self._get_json(device, _READ_PATH)
        metrics = parse_gauge_response(body)
        return DeviceReading(metrics=metrics)

    def _get_json(self, device: dict[str, Any], path: str) -> Any:
        url = f"{device_base_url(device)}{path}"
        try:
            if self._client is not None:
                response = self._client.get(url, timeout=self._timeout_for(device))
            else:
                with httpx.Client(timeout=self._timeout_for(device)) as client:
                    response = client.get(url)
        except httpx.TimeoutException as exc:
            raise DeviceDriverError(
                f"Timeout ao contactar dispositivo em {url}.",
                code="timeout",
            ) from exc
        except httpx.RequestError as exc:
            raise DeviceDriverError(
                f"Falha de rede ao contactar dispositivo em {url}: {exc}",
                code="network_error",
            ) from exc

        return self._parse_http_response(response, url=url)

    def _parse_http_response(self, response: httpx.Response, *, url: str) -> Any:
        if response.status_code >= 400:
            raise DeviceDriverError(
                f"Dispositivo respondeu HTTP {response.status_code} em {url}.",
                code="http_error",
            )
        try:
            return response.json()
        except ValueError as exc:
            raise DeviceDriverError(
                f"Resposta JSON inválida do dispositivo em {url}.",
                code="invalid_response",
            ) from exc


__all__ = ["Esp8266GaugeDriver"]
