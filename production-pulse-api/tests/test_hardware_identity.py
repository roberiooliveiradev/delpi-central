from __future__ import annotations

import httpx

from production_pulse_app.domain.services.hardware_identity_normalize_service import (
    classify_identity,
    normalize_mac_address,
)
from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver


def test_normalize_mac_variants():
    assert normalize_mac_address("aa:bb:cc:11:22:33") == "AA:BB:CC:11:22:33"
    assert normalize_mac_address("AA-BB-CC-11-22-33") == "AA:BB:CC:11:22:33"
    assert normalize_mac_address("AABBCC112233") == "AA:BB:CC:11:22:33"
    assert normalize_mac_address("bad") is None


def test_classify_identity_priority():
    assert classify_identity(
        hardware_uid="ESP-1",
        controller_code="ESP-1",
        mac_address="AA:BB:CC:11:22:33",
    )[1] == "strong"
    assert classify_identity(
        hardware_uid=None,
        controller_code="ESP-1",
        mac_address="AA:BB:CC:11:22:33",
    )[1] == "controller_code"
    assert classify_identity(
        hardware_uid=None,
        controller_code=None,
        mac_address="AA:BB:CC:11:22:33",
    )[1] == "mac_fallback"
    assert classify_identity(
        hardware_uid=None,
        controller_code=None,
        mac_address=None,
    )[1] == "legacy_unknown"


def test_counter_read_includes_identity_without_status_call():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        assert request.url.path == "/api/contador"
        return httpx.Response(
            200,
            json={
                "contador": 42,
                "hardwareUid": "ESP-00ABCDEF",
                "controllerCode": "ESP-00ABCDEF",
                "mac": "aa:bb:cc:dd:ee:ff",
            },
        )

    driver = Esp8266CounterDriver(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        timeout_seconds=1.0,
    )
    reading = driver.read({"ip_address": "192.168.20.2", "driver_key": "esp8266_counter_v1"})
    assert reading.metrics == {"counter": 42}
    assert reading.meta["hardwareUid"] == "ESP-00ABCDEF"
    assert reading.meta["mac"] == "AA:BB:CC:DD:EE:FF"
    assert calls == ["/api/contador"]
