from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_config_push_service import (
    DeviceConfigPushService,
    request_changes_chip_config,
)
from production_pulse_app.domain.models.device_reading import CommandResult


class _FakeDriver:
    def __init__(self) -> None:
        self.last_payload: dict[str, Any] | None = None
        self.calls = 0

    def execute(self, device: dict[str, Any], command: str, payload: dict[str, Any] | None = None):
        self.calls += 1
        self.last_payload = dict(payload or {})
        return CommandResult(success=True, response_payload={"ok": True})


class _FakeRegistry:
    def __init__(self, driver: _FakeDriver) -> None:
        self._driver = driver

    def build_capabilities(self, driver_key: str) -> dict[str, Any]:
        return {"commands": ["configure", "reboot"]}

    def get_implementation(self, driver_key: str) -> _FakeDriver:
        return self._driver


def _device(**overrides):
    base = {
        "id": "d1",
        "driver_key": "esp8266_counter_v1",
        "branch": "01",
        "ip_address": "192.168.20.2",
        "wifi_ssid": "Delpi-Desenvolvimento",
        "debounce_ms": 100,
        "device_api_token": "tok",
    }
    base.update(overrides)
    return base


def test_request_changes_chip_config_ignores_poll_echo():
    row = _device()
    payload = {
        "name": "ESP8266-001",
        "branch": "01",
        "wifiSsid": "Delpi-Desenvolvimento",
        "debounceMs": 100,
        "pollIntervalMs": 300,
        "enabled": True,
    }
    assert request_changes_chip_config(row, payload) is False


def test_request_changes_chip_config_detects_ssid_change():
    row = _device()
    assert request_changes_chip_config(row, {"wifiSsid": "Other"}) is True


def test_request_changes_chip_config_detects_new_token():
    row = _device()
    assert request_changes_chip_config(row, {"apiToken": "new-secret"}) is True
    assert request_changes_chip_config(row, {"apiToken": ""}) is False


def test_push_skips_pulse_only_poll_update(monkeypatch):
    driver = _FakeDriver()
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(driver))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    result = service.push_after_save(
        _device(poll_interval_ms=300),
        request_payload={
            "name": "ESP8266-001",
            "branch": "01",
            "wifiSsid": "Delpi-Desenvolvimento",
            "debounceMs": 100,
            "pollIntervalMs": 300,
            "enabled": True,
        },
        force_ota_provision=False,
        previous_row=_device(poll_interval_ms=30000),
    )

    assert result["status"] == "skipped"
    assert "não foi contactado" in result["message"].lower() or "poll" in result["message"].lower()
    assert driver.calls == 0


def test_push_skips_replace_echo_without_force_ota(monkeypatch):
    """MFE edit uses PUT replace with full form echo — must not force chip push."""
    driver = _FakeDriver()
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(driver))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    previous = _device()
    result = service.push_after_save(
        previous,
        request_payload={
            "name": "ESP8266-001",
            "branch": "01",
            "ipAddress": "192.168.20.2",
            "driverKey": "esp8266_http_v1",
            "wifiSsid": "Delpi-Desenvolvimento",
            "debounceMs": 100,
            "pollIntervalMs": 300,
            "enabled": True,
            "controllerCode": "ESP-00B7942B",
            "apiToken": "",
            "wifiPassword": "",
        },
        force_ota_provision=False,
        previous_row=previous,
    )

    assert result["status"] == "skipped"
    assert driver.calls == 0


def test_push_still_runs_when_replace_would_have_forced_but_ssid_changed(monkeypatch):
    driver = _FakeDriver()
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(driver))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    result = service.push_after_save(
        _device(wifi_ssid="Nova-Rede"),
        request_payload={
            "wifiSsid": "Nova-Rede",
            "debounceMs": 100,
            "branch": "01",
        },
        force_ota_provision=False,
        previous_row=_device(wifi_ssid="Delpi-Desenvolvimento"),
    )

    assert result["status"] == "ok"
    assert driver.calls == 1


def test_push_after_create_force_includes_ota_fields(monkeypatch):
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
        _device(),
        request_payload={},
        force_ota_provision=True,
    )

    assert result["status"] == "ok"
    assert driver.last_payload is not None
    assert driver.last_payload["otaBaseUrl"] == "http://192.168.1.10/apps/production-pulse-api"
    assert driver.last_payload["branch"] == "01"
    assert driver.last_payload["otaCheckIntervalMs"] == 60000


def test_push_on_token_change_hits_chip(monkeypatch):
    driver = _FakeDriver()
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(driver))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    previous = _device(device_api_token="old")
    result = service.push_after_save(
        _device(device_api_token="new-secret"),
        request_payload={
            "wifiSsid": "Delpi-Desenvolvimento",
            "debounceMs": 100,
            "branch": "01",
            "apiToken": "new-secret",
            "pollIntervalMs": 300,
        },
        previous_row=previous,
    )

    assert result["status"] == "ok"
    assert driver.calls == 1
    assert driver.last_payload is not None
    assert driver.last_payload.get("apiToken") == "new-secret"


class _UnauthorizedDriver:
    def execute(self, device, command, payload=None):
        return CommandResult(success=False, error_code="unauthorized")


def test_push_maps_unauthorized_to_specific_message(monkeypatch):
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(_UnauthorizedDriver()))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    result = service.push_after_save(
        _device(device_api_token="stale-token"),
        request_payload={"apiToken": "stale-token", "wifiSsid": "Other"},
        previous_row=_device(wifi_ssid="Delpi-Desenvolvimento"),
    )

    assert result["status"] == "failed"
    assert result["errorCode"] == "unauthorized"
    assert "token" in result["message"].lower()


def test_push_maps_unauthorized_without_cadastro_token_to_missing_token(monkeypatch):
    service = DeviceConfigPushService()
    monkeypatch.setattr(service, "_registry", _FakeRegistry(_UnauthorizedDriver()))
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_config_push_service.settings.PP_DEVICE_OTA_BASE_URL",
        "http://192.168.1.10/apps/production-pulse-api",
    )

    result = service.push_after_save(
        _device(device_api_token=None),
        request_payload={"wifiSsid": "Other"},
        force_ota_provision=False,
        previous_row=_device(wifi_ssid="Delpi-Desenvolvimento", device_api_token=None),
    )

    assert result["status"] == "failed"
    assert result["errorCode"] == "missing_token"
    assert "token" in result["message"].lower()
