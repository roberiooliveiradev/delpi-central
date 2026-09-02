from __future__ import annotations

import httpx
import pytest

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver
from production_pulse_app.startup.register_device_drivers import (
    register_device_drivers,
    reset_device_driver_registration_for_tests,
)

_DEVICE = {"ip_address": "192.168.20.2", "driver_key": "esp8266_counter_v1"}


def _mock_transport(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_read_normalizes_counter_metric():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/contador"
        return httpx.Response(200, json={"contador": 1284})

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.read(_DEVICE)
    assert reading.metrics == {"counter": 1284}


def test_read_timeout_raises_device_driver_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=0.1)
    with pytest.raises(DeviceDriverError) as exc_info:
        driver.read(_DEVICE)
    assert exc_info.value.code == "timeout"


def test_execute_increment_returns_updated_counter():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/incrementar"
        assert request.method == "POST"
        return httpx.Response(200, json={"contador": 1285})

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "increment")
    assert result.success is True
    assert result.metrics == {"counter": 1285}


def test_execute_reset_returns_zero():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/reset"
        return httpx.Response(200, json={"contador": 0})

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "reset")
    assert result.success is True
    assert result.metrics == {"counter": 0}


def test_execute_network_error_returns_code_only():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "increment")
    assert result.success is False
    assert result.error_code == "network_error"
    assert result.error_message is None


def test_execute_unknown_command_returns_failure():
    driver = Esp8266CounterDriver(timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "reboot")
    assert result.success is False
    assert result.error_code == "unsupported_command"


def test_register_device_drivers_exposes_implementation():
    reset_device_driver_registration_for_tests()
    with pytest.raises(DeviceDriverNotImplementedError):
        get_device_driver_registry().get_implementation("esp8266_counter_v1")

    register_device_drivers()
    driver = get_device_driver_registry().get_implementation("esp8266_counter_v1")
    assert isinstance(driver, Esp8266CounterDriver)
    assert driver.capabilities() == frozenset({"increment", "decrement", "reset"})

    reset_device_driver_registration_for_tests()
