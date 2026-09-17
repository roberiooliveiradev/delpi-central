from __future__ import annotations

from production_pulse_app.domain.services.device_led_state import normalize_led_state
from production_pulse_app.domain.services.device_serialization_service import device_row_to_api


def test_normalize_led_state_positive_backend_ok():
    assert normalize_led_state("backend_ok") == "backend_ok"


def test_normalize_led_state_sibling_never_contacted():
    assert normalize_led_state("wifi_ok_never_contacted") == "wifi_ok_never_contacted"


def test_normalize_led_state_negative_unknown_or_empty():
    assert normalize_led_state(None) is None
    assert normalize_led_state("") is None
    assert normalize_led_state("online") is None
    assert normalize_led_state("  ") is None


def test_device_row_to_api_exposes_led_state():
    payload = device_row_to_api(
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "branch": "filial-01",
            "name": "ESP",
            "ip_address": "192.168.1.10",
            "driver_key": "esp8266_counter_v1",
            "role_key": "pulse_counter",
            "enabled": True,
            "poll_interval_ms": 1000,
            "led_state": "backend_ok",
            "last_metrics": {"counter": 1},
        }
    )
    assert payload["ledState"] == "backend_ok"


def test_device_row_to_api_led_state_absent_when_null():
    payload = device_row_to_api(
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "branch": "filial-01",
            "name": "ESP",
            "ip_address": "192.168.1.10",
            "driver_key": "esp8266_counter_v1",
            "role_key": "pulse_counter",
            "enabled": True,
            "poll_interval_ms": 1000,
            "led_state": None,
            "last_metrics": {},
        }
    )
    assert payload["ledState"] is None
