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
            return CommandResult(
                success=False,
                error_message=f"Comando não suportado: {command_key}",
            )

        try:
            response_body = self._post_json(device, path, payload=payload)
            counter = parse_counter_response(response_body)
            return CommandResult(
                success=True,
                metrics={"counter": counter},
                response_payload=response_body if isinstance(response_body, dict) else {},
            )
        except DeviceDriverError as exc:
            return CommandResult(success=False, error_message=str(exc))

    def _fetch_counter(self, device: dict[str, Any]) -> DeviceReading:
        body = self._get_json(device, _READ_PATH)
        counter = parse_counter_response(body)
        return DeviceReading(metrics={"counter": counter})

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

    def _post_json(
        self,
        device: dict[str, Any],
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{device_base_url(device)}{path}"
        json_body = payload or {}
        try:
            if self._client is not None:
                response = self._client.post(url, json=json_body, timeout=self._timeout_for(device))
            else:
                with httpx.Client(timeout=self._timeout_for(device)) as client:
                    response = client.post(url, json=json_body)
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


__all__ = ["Esp8266CounterDriver"]
