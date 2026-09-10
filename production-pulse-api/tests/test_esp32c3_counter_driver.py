from __future__ import annotations

import httpx
import pytest

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.infrastructure.drivers.esp32c3_counter_driver import Esp32c3CounterDriver
from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver
from production_pulse_app.startup.register_device_drivers import (
    register_device_drivers,
    reset_device_driver_registration_for_tests,
)

_DEVICE = {"ip_address": "192.168.20.3", "driver_key": "esp32c3_counter_v1"}


def _mock_transport(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_c3_read_uses_same_counter_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/contador"
        return httpx.Response(200, json={"contador": 42})

    driver = Esp32c3CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.read(_DEVICE)
    assert reading.metrics == {"counter": 42}
    assert driver.driver_key == "esp32c3_counter_v1"


def test_c3_status_accepts_additive_input_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/contador":
            return httpx.Response(200, json={"contador": 7})
        if request.url.path == "/api/status":
            return httpx.Response(
                200,
                json={
                    "controllerCode": "ESP32C3-AABBCCDDEEFF",
                    "codigoControlador": "ESP32C3-AABBCCDDEEFF",
                    "equipamento": "ESP32C3-AABBCCDDEEFF",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "firmwareVersion": "esp32c3_counter_v1.0.0",
                    "input1": 1,
                    "input2": 0,
                    "wifiConnected": True,
                },
            )
        if request.url.path == "/api/config":
            return httpx.Response(
                200,
                json={
                    "ssid": "PlantWifi",
                    "debounceMs": 100,
                    "passwordSet": True,
                    "apiTokenSet": True,
                    "wifiConfigured": True,
                },
            )
        return httpx.Response(404)

    driver = Esp32c3CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.test(_DEVICE)
    assert reading.metrics == {"counter": 7}
    assert reading.meta["controllerCode"] == "ESP32C3-AABBCCDDEEFF"
    assert reading.meta["mac"] == "AA:BB:CC:DD:EE:FF"
    # Additive fields must not break parsing; they are ignored until a consumer needs them.
    assert "input1" not in reading.meta


def test_c3_and_esp8266_share_capabilities():
    assert Esp32c3CounterDriver().capabilities() == Esp8266CounterDriver().capabilities()


def test_register_exposes_c3_implementation():
    reset_device_driver_registration_for_tests()
    register_device_drivers()
    registry = get_device_driver_registry()
    driver = registry.get_implementation("esp32c3_counter_v1")
    assert isinstance(driver, Esp32c3CounterDriver)
    resolved = registry.resolve_driver("esp32c3_counter_v1")
    assert resolved.role_key == "pulse_counter"
    assert "increment" in (resolved.definition.get("commands") or [])
    reset_device_driver_registration_for_tests()
