from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_config_push_service import (
    DeviceConfigPushService,
)
from production_pulse_app.domain.models.device_reading import CommandResult


class _FakeDriver:
    def __init__(self) -> None:
        self.last_payload: dict[str, Any] | None = None

    def execute(self, device: dict[str, Any], command: str, payload: dict[str, Any] | None = None):
        self.last_payload = dict(payload or {})
        return CommandResult(success=True, response_payload={"ok": True})


class _FakeRegistry:
    def __init__(self, driver: _FakeDriver) -> None:
        self._driver = driver

    def build_capabilities(self, driver_key: str) -> dict[str, Any]:
        return {"commands": ["configure", "reboot"]}

    def get_implementation(self, driver_key: str) -> _FakeDriver:
        return self._driver


def test_push_after_save_always_includes_ota_fields(monkeypatch):
    driver = _FakeDriver()
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(driver))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_CHECK_INTERVAL_MS",
        60000,
    )

    result = service.push_after_save(
        {
            "id": "d1",
            "driver_key": "esp8266_counter_v1",
            "branch": "01",
            "ip_address": "10.0.0.8",
            "device_api_token": "tok",
        },
        request_payload={},  # no wifi change — OTA provision must still run
    )

    assert result["status"] == "ok"
    assert driver.last_payload is not None
    assert driver.last_payload["otaBaseUrl"] == "http://192.168.1.10/apps/production-pulse-api"
    assert driver.last_payload["branch"] == "01"
    assert driver.last_payload["otaCheckIntervalMs"] == 60000
