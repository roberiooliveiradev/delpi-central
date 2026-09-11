from __future__ import annotations

import httpx

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.infrastructure.drivers.esp32_counter_driver import Esp32CounterDriver
from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver
from production_pulse_app.startup.register_device_drivers import (
    register_device_drivers,
    reset_device_driver_registration_for_tests,
)

_DEVICE = {"ip_address": "192.168.20.4", "driver_key": "esp32_counter_v1"}


def _mock_transport(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_wroom_read_uses_same_counter_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/contador"
        return httpx.Response(200, json={"contador": 11})

    driver = Esp32CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.read(_DEVICE)
    assert reading.metrics == {"counter": 11}
    assert driver.driver_key == "esp32_counter_v1"


def test_wroom_shares_capabilities_with_esp8266():
    assert Esp32CounterDriver().capabilities() == Esp8266CounterDriver().capabilities()
    assert "ota_wake" not in Esp32CounterDriver().capabilities()


def test_register_exposes_wroom_implementation(plugins_db_env):
    reset_device_driver_registration_for_tests()
    register_device_drivers()
    registry = get_device_driver_registry()
    driver = registry.get_implementation("esp32_counter_v1")
    assert isinstance(driver, Esp32CounterDriver)
    resolved = registry.resolve_driver("esp32_counter_v1")
    assert resolved.role_key == "pulse_counter"
    assert "increment" in (resolved.definition.get("commands") or [])
    assert "ota_wake" not in (resolved.definition.get("commands") or [])
    reset_device_driver_registration_for_tests()
