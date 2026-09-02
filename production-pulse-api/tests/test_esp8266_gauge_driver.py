from __future__ import annotations

import httpx
import pytest

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.infrastructure.drivers.device_http_support import parse_gauge_response
from production_pulse_app.infrastructure.drivers.esp8266_gauge_driver import Esp8266GaugeDriver
from production_pulse_app.startup.register_device_drivers import (
    register_device_drivers,
    reset_device_driver_registration_for_tests,
)

_DEVICE = {"ip_address": "192.168.20.3", "driver_key": "esp8266_gauge_v1"}


def _mock_transport(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parse_gauge_response_accepts_portuguese_keys():
    metrics = parse_gauge_response({"rpm": 1180, "temperatura": 67.2})
    assert metrics == {"rpm": 1180.0, "temperature_c": 67.2}


def test_parse_gauge_response_accepts_canonical_keys():
    metrics = parse_gauge_response({"rpm": 1850, "temperature_c": 42.1})
    assert metrics == {"rpm": 1850.0, "temperature_c": 42.1}


def test_parse_gauge_response_requires_at_least_one_metric():
    with pytest.raises(DeviceDriverError, match="rpm ou temperatura"):
        parse_gauge_response({"status": "ok"})


def test_read_normalizes_gauge_metrics():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/sensores"
        return httpx.Response(200, json={"rpm": 1180, "temperatura": 42.1})

    driver = Esp8266GaugeDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.read(_DEVICE)
    assert reading.metrics == {"rpm": 1180.0, "temperature_c": 42.1}


def test_read_timeout_raises_device_driver_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    driver = Esp8266GaugeDriver(client=_mock_transport(handler), timeout_seconds=0.1)
    with pytest.raises(DeviceDriverError, match="Timeout"):
        driver.read(_DEVICE)


def test_execute_any_command_returns_failure():
    driver = Esp8266GaugeDriver(timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "reset")
    assert result.success is False
    assert "não suportado" in (result.error_message or "")


def test_register_device_drivers_exposes_gauge_implementation():
    reset_device_driver_registration_for_tests()
    with pytest.raises(DeviceDriverNotImplementedError):
        get_device_driver_registry().get_implementation("esp8266_gauge_v1")

    register_device_drivers()
    driver = get_device_driver_registry().get_implementation("esp8266_gauge_v1")
    assert isinstance(driver, Esp8266GaugeDriver)
    assert driver.capabilities() == frozenset()

    reset_device_driver_registration_for_tests()
