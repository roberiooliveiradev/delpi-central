from __future__ import annotations

from typing import Any

import httpx

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.domain.models.device_reading import CommandResult, DeviceReading
from production_pulse_app.domain.services.device_config_payload_service import (
    build_configure_http_payload,
)
from production_pulse_app.infrastructure.drivers.device_http_support import (
    device_get_json,
    device_post_json,
    parse_counter_response,
    parse_device_config_response,
)

_DRIVER_KEY = "esp8266_counter_v1"
_READ_PATH = "/api/contador"
_STATUS_PATH = "/api/status"
_CONFIG_PATH = "/api/config"
_COMMAND_PATHS = {
    "increment": "/api/incrementar",
    "decrement": "/api/decrementar",
    "reset": "/api/reset",
    "set": "/api/definir",
    "reboot": "/api/reboot",
    "factory_reset": "/api/factory-reset",
}
_CAPABILITIES = frozenset(
    {"increment", "decrement", "reset", "set", "configure", "reboot", "factory_reset"}
)


def parse_controller_identity(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    code = body.get("controllerCode") or body.get("codigoControlador") or body.get("equipamento")
    payload: dict[str, Any] = {}
    if code is not None and str(code).strip():
        payload["controllerCode"] = str(code).strip()
    mac = body.get("mac")
    if mac is not None and str(mac).strip():
        payload["mac"] = str(mac).strip()
    ip = body.get("ip")
    if ip is not None and str(ip).strip():
        payload["ip"] = str(ip).strip()
    for key in ("firmwareVersion", "uptimeMs", "freeHeap", "rssi", "wifiConnected"):
        if key in body and body.get(key) is not None:
            payload[key] = body.get(key)
    return payload


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
        reading = self._fetch_counter(device)
        meta: dict[str, Any] = {}
        identity = self._fetch_identity(device)
        if identity:
            meta.update(identity)
        config = self.get_config(device)
        if config:
            meta["deviceConfig"] = config
        if not meta:
            return reading
        return DeviceReading(metrics=reading.metrics, meta=meta)

    def get_config(self, device: dict[str, Any]) -> dict[str, Any]:
        try:
            body = device_get_json(
                device,
                _CONFIG_PATH,
                client=self._client,
                timeout_seconds=self._timeout_for(device),
            )
        except DeviceDriverError:
            return {}
        return parse_device_config_response(body)

    def execute(
        self,
        device: dict[str, Any],
        command_key: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> CommandResult:
        normalized = (command_key or "").strip().lower()
        if normalized == "configure":
            return self._execute_configure(device, payload)

        path = _COMMAND_PATHS.get(normalized)
        if path is None:
            return CommandResult(success=False, error_code="unsupported_command")

        body: dict[str, Any] | None = None
        if normalized == "set":
            counter = self._resolve_set_counter(payload)
            if counter is None:
                return CommandResult(success=False, error_code="invalid_command_payload")
            body = {"contador": counter}

        try:
            response_body = device_post_json(
                device,
                path,
                client=self._client,
                timeout_seconds=self._timeout_for(device),
                payload=body,
            )
            if normalized in {"reboot", "factory_reset"}:
                return CommandResult(
                    success=True,
                    metrics={},
                    response_payload=response_body if isinstance(response_body, dict) else {},
                )
            counter = parse_counter_response(response_body)
            return CommandResult(
                success=True,
                metrics={"counter": counter},
                response_payload=response_body if isinstance(response_body, dict) else {},
            )
        except DeviceDriverError as exc:
            return CommandResult(success=False, error_code=exc.code)

    def _execute_configure(
        self,
        device: dict[str, Any],
        payload: dict[str, Any] | None,
    ) -> CommandResult:
        body = build_configure_http_payload(payload)
        if not body:
            return CommandResult(success=False, error_code="invalid_command_payload")
        try:
            response_body = device_post_json(
                device,
                _CONFIG_PATH,
                client=self._client,
                timeout_seconds=self._timeout_for(device),
                payload=body,
            )
            return CommandResult(
                success=True,
                metrics={},
                response_payload=parse_device_config_response(response_body),
            )
        except DeviceDriverError as exc:
            return CommandResult(success=False, error_code=exc.code)

    @staticmethod
    def _resolve_set_counter(payload: dict[str, Any] | None) -> int | None:
        if not isinstance(payload, dict):
            return None
        raw = payload.get("counter")
        if raw is None:
            raw = payload.get("contador")
        if raw is None:
            return None
        try:
            if isinstance(raw, bool):
                return None
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _fetch_counter(self, device: dict[str, Any]) -> DeviceReading:
        body = device_get_json(
            device,
            _READ_PATH,
            client=self._client,
            timeout_seconds=self._timeout_for(device),
        )
        counter = parse_counter_response(body)
        return DeviceReading(metrics={"counter": counter})

    def _fetch_identity(self, device: dict[str, Any]) -> dict[str, Any]:
        try:
            body = device_get_json(
                device,
                _STATUS_PATH,
                client=self._client,
                timeout_seconds=self._timeout_for(device),
            )
        except DeviceDriverError:
            return {}
        return parse_controller_identity(body)


__all__ = ["Esp8266CounterDriver", "parse_controller_identity"]
