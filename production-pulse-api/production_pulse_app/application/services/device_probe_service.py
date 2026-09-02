from __future__ import annotations

import time
from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.application.services.test_probe_rate_limiter import (
    TestProbeRateLimitError,
    get_test_probe_rate_limiter,
)
from production_pulse_app.domain.errors import DeviceDriverError, DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import (
    normalize_ip_address,
    resolve_driver,
    validate_branch,
)
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    device_connectivity_user_message,
)


class DeviceProbeService:
    def probe_device(
        self,
        *,
        branch: str,
        ip_address: str,
        driver_key: str,
        actor_sub: str | None,
        api_token: str | None = None,
    ) -> dict[str, Any]:
        get_test_probe_rate_limiter().check(actor_sub or "anonymous")
        validate_branch(branch)
        ip = normalize_ip_address(ip_address)
        resolved = resolve_driver(driver_key)
        device_stub: dict[str, Any] = {
            "branch": branch,
            "ip_address": ip,
            "driver_key": resolved.driver_key,
        }
        token = (api_token or "").strip()
        if token:
            device_stub["device_api_token"] = token
        return self._run_probe(resolved.driver_key, device_stub)

    def probe_existing_device(self, device: dict[str, Any], *, actor_sub: str | None) -> dict[str, Any]:
        get_test_probe_rate_limiter().check(actor_sub or "anonymous")
        return self._run_probe(str(device["driver_key"]), device)

    def _probe_failure_payload(
        self,
        driver_key: str,
        *,
        code: str,
        latency_ms: int,
        fallback: str | None = None,
    ) -> dict[str, Any]:
        return {
            "driverKey": driver_key,
            "online": False,
            "error": code,
            "errorMessage": device_connectivity_user_message(code, fallback=fallback),
            "latencyMs": latency_ms,
        }

    def _run_probe(self, driver_key: str, device: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            driver = get_device_driver_registry().get_implementation(driver_key)
        except DeviceDriverNotImplementedError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return self._probe_failure_payload(
                driver_key,
                code="driver_not_implemented",
                latency_ms=latency_ms,
                fallback=str(exc),
            )

        try:
            reading = driver.test(device)
            latency_ms = int((time.perf_counter() - started) * 1000)
            payload: dict[str, Any] = {
                "driverKey": driver_key,
                "metrics": reading.metrics,
                "latencyMs": latency_ms,
                "online": True,
            }
            meta = reading.meta if isinstance(reading.meta, dict) else {}
            controller_code = meta.get("controllerCode")
            if controller_code:
                payload["controllerCode"] = controller_code
            if meta.get("mac"):
                payload["mac"] = meta["mac"]
            device_config = meta.get("deviceConfig")
            if isinstance(device_config, dict) and device_config:
                payload["deviceConfig"] = device_config
                if device_config.get("ssid"):
                    payload["wifiSsid"] = device_config["ssid"]
                if "debounceMs" in device_config:
                    payload["debounceMs"] = device_config["debounceMs"]
                if "apiTokenSet" in device_config:
                    payload["apiTokenSet"] = bool(device_config["apiTokenSet"])
            for key in ("firmwareVersion", "uptimeMs", "freeHeap", "rssi", "wifiConnected"):
                if key in meta and meta.get(key) is not None:
                    payload[key] = meta[key]
            return payload
        except DeviceDriverError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return self._probe_failure_payload(
                driver_key,
                code=exc.code,
                latency_ms=latency_ms,
                fallback=exc.technical_detail,
            )


__all__ = [
    "DeviceProbeService",
    "DeviceValidationError",
    "TestProbeRateLimitError",
]
