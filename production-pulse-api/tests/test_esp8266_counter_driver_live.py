from __future__ import annotations

import os

import httpx
import pytest

from production_pulse_app.infrastructure.drivers.esp8266_counter_driver import Esp8266CounterDriver

_LIVE_IP = os.getenv("PP_LIVE_ESP_IP", "192.168.20.2").strip()


@pytest.mark.live
def test_live_read_counter_from_pilot_esp():
    if os.getenv("PP_LIVE_ESP") != "1":
        pytest.skip("Defina PP_LIVE_ESP=1 para teste live com ESP8266 piloto.")

    driver = Esp8266CounterDriver(timeout_seconds=3.0)
    reading = driver.read(
        {
            "ip_address": _LIVE_IP,
            "driver_key": "esp8266_counter_v1",
        }
    )
    assert isinstance(reading.metrics.get("counter"), int)
    assert reading.metrics["counter"] >= 0
