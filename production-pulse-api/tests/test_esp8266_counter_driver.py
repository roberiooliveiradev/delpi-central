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


def test_probe_test_includes_controller_code_from_status():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/contador":
            return httpx.Response(200, json={"contador": 10})
        if request.url.path == "/api/status":
            return httpx.Response(
                200,
                json={
                    "codigoControlador": "ESP-00ABCDEF",
                    "contador": 10,
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "firmwareVersion": "esp8266_counter_v1.1.0",
                    "uptimeMs": 60000,
                    "freeHeap": 32000,
                    "rssi": -55,
                    "wifiConnected": True,
                },
            )
        if request.url.path == "/api/config":
            return httpx.Response(
                200,
                json={
                    "ssid": "FactoryNet",
                    "debounceMs": 100,
                    "passwordSet": True,
                    "apiTokenSet": False,
                    "wifiConfigured": True,
                },
            )
        return httpx.Response(404)

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    reading = driver.test(_DEVICE)
    assert reading.metrics == {"counter": 10}
    assert reading.meta["controllerCode"] == "ESP-00ABCDEF"
    assert reading.meta["mac"] == "AA:BB:CC:DD:EE:FF"
    assert reading.meta["firmwareVersion"] == "esp8266_counter_v1.1.0"
    assert reading.meta["rssi"] == -55
    assert reading.meta["deviceConfig"]["ssid"] == "FactoryNet"


def test_configure_posts_config_payload():
    import json

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/config"
        assert request.method == "POST"
        assert request.headers.get("X-Device-Token") == "secret-token"
        body = json.loads(request.content.decode("utf-8"))
        assert body["ssid"] == "PlantWifi"
        assert body["debounceMs"] == 80
        return httpx.Response(
            200,
            json={
                "ssid": "PlantWifi",
                "debounceMs": 80,
                "passwordSet": True,
                "apiTokenSet": True,
                "wifiConfigured": True,
            },
        )

    device = {**_DEVICE, "device_api_token": "secret-token"}
    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(
        device,
        "configure",
        payload={"wifiSsid": "PlantWifi", "debounceMs": 80},
    )
    assert result.success is True
    assert result.response_payload["ssid"] == "PlantWifi"


def test_device_http_injects_token_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Device-Token") == "tok-1"
        assert request.url.path == "/api/status"
        return httpx.Response(200, json={"controllerCode": "ESP-1", "contador": 1})

    device = {**_DEVICE, "apiToken": "tok-1"}
    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    meta = driver._fetch_identity(device)
    assert meta["controllerCode"] == "ESP-1"


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
    result = driver.execute(_DEVICE, "not_a_real_command")
    assert result.success is False
    assert result.error_code == "unsupported_command"


def test_execute_set_posts_definir_with_contador():
    import json

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/definir"
        assert request.method == "POST"
        body = json.loads(request.content.decode("utf-8"))
        assert body == {"contador": 1500}
        return httpx.Response(200, json={"contador": 1500})

    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "set", payload={"counter": 1500})
    assert result.success is True
    assert result.metrics == {"counter": 1500}


def test_execute_set_without_payload_fails():
    driver = Esp8266CounterDriver(timeout_seconds=1.0)
    result = driver.execute(_DEVICE, "set", payload=None)
    assert result.success is False
    assert result.error_code == "invalid_command_payload"


def test_register_device_drivers_exposes_implementation():
    reset_device_driver_registration_for_tests()
    with pytest.raises(DeviceDriverNotImplementedError):
        get_device_driver_registry().get_implementation("esp8266_counter_v1")

    register_device_drivers()
    driver = get_device_driver_registry().get_implementation("esp8266_counter_v1")
    assert isinstance(driver, Esp8266CounterDriver)
    assert driver.capabilities() == frozenset(
        {"increment", "decrement", "reset", "set", "configure", "reboot", "factory_reset"}
    )

    reset_device_driver_registration_for_tests()


def test_reboot_posts_authenticated_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/reboot"
        assert request.method == "POST"
        assert request.headers.get("X-Device-Token") == "secret-token"
        return httpx.Response(200, json={"ok": True, "action": "reboot"})

    device = {**_DEVICE, "device_api_token": "secret-token"}
    driver = Esp8266CounterDriver(client=_mock_transport(handler), timeout_seconds=1.0)
    result = driver.execute(device, "reboot")
    assert result.success is True
