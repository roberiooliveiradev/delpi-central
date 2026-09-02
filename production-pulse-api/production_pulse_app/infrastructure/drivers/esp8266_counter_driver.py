from __future__ import annotations

from typing import Any

import httpx

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.domain.models.device_reading import CommandResult, DeviceReading
from production_pulse_app.infrastructure.drivers.device_http_support import (
    device_get_json,
    device_post_json,
    parse_counter_response,
)

_DRIVER_KEY = "esp8266_counter_v1"
_READ_PATH = "/api/contador"
_COMMAND_PATHS = {
    "increment": "/api/incrementar",
    "decrement": "/api/decrementar",
    "reset": "/api/reset",
}
_CAPABILITIES = frozenset({"increment", "decrement", "reset"})


class Esp8266CounterDriver:
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
        return _CAPABILITIES

    def read(self, device: dict[str, Any]) -> DeviceReading:
        return self._fetch_counter(device)

    def test(self, device: dict[str, Any]) -> DeviceReading:
        return self.read(device)

    def execute(
        self,
        device: dict[str, Any],
        command_key: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> CommandResult:
        normalized = (command_key or "").strip().lower()
        path = _COMMAND_PATHS.get(normalized)
        if path is None:
            return CommandResult(success=False, error_code="unsupported_command")

        try:
            response_body = device_post_json(
                device,
                path,
                client=self._client,
                timeout_seconds=self._timeout_for(device),
                payload=payload,
            )
            counter = parse_counter_response(response_body)
            return CommandResult(
                success=True,
                metrics={"counter": counter},
                response_payload=response_body if isinstance(response_body, dict) else {},
            )
        except DeviceDriverError as exc:
            return CommandResult(success=False, error_code=exc.code)

    def _fetch_counter(self, device: dict[str, Any]) -> DeviceReading:
        body = device_get_json(
            device,
            _READ_PATH,
            client=self._client,
            timeout_seconds=self._timeout_for(device),
        )
        counter = parse_counter_response(body)
        return DeviceReading(metrics={"counter": counter})


__all__ = ["Esp8266CounterDriver"]
