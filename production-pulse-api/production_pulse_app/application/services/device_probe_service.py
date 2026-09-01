from __future__ import annotations

import time
from typing import Any
from uuid import UUID

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


class DeviceProbeService:
    def probe_device(
        self,
        *,
        branch: str,
        ip_address: str,
        driver_key: str,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        get_test_probe_rate_limiter().check(actor_sub or "anonymous")
        validate_branch(branch)
        ip = normalize_ip_address(ip_address)
        resolved = resolve_driver(driver_key)
        device_stub = {
            "branch": branch,
            "ip_address": ip,
            "driver_key": resolved.driver_key,
        }
        return self._run_probe(resolved.driver_key, device_stub)

    def probe_existing_device(self, device: dict[str, Any], *, actor_sub: str | None) -> dict[str, Any]:
        get_test_probe_rate_limiter().check(actor_sub or "anonymous")
        return self._run_probe(str(device["driver_key"]), device)

    def _run_probe(self, driver_key: str, device: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            driver = get_device_driver_registry().get_implementation(driver_key)
        except DeviceDriverNotImplementedError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "driverKey": driver_key,
                "online": False,
                "error": "driver_not_implemented",
                "latencyMs": latency_ms,
            }

        try:
            reading = driver.test(device)
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "driverKey": driver_key,
                "metrics": reading.metrics,
                "latencyMs": latency_ms,
                "online": True,
            }
        except DeviceDriverError as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return {
                "driverKey": driver_key,
                "online": False,
                "error": exc.code,
                "latencyMs": latency_ms,
            }


__all__ = [
    "DeviceProbeService",
    "DeviceValidationError",
    "TestProbeRateLimitError",
]
