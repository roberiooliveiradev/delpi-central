from __future__ import annotations

from typing import Any

import httpx

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.models.device_reading import CommandResult, DeviceReading
from production_pulse_app.infrastructure.drivers.device_http_support import (
    device_get_json,
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
            return CommandResult(success=False, error_code="unsupported_command")
        return CommandResult(success=False, error_code="unsupported_command")

    def _fetch_gauge(self, device: dict[str, Any]) -> DeviceReading:
        body = device_get_json(
            device,
            _READ_PATH,
            client=self._client,
            timeout_seconds=self._timeout_for(device),
        )
        metrics = parse_gauge_response(body)
        return DeviceReading(metrics=metrics)


__all__ = ["Esp8266GaugeDriver"]
