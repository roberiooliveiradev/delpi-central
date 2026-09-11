from __future__ import annotations

from production_pulse_app.domain.services.device_config_payload_service import (
    build_configure_http_payload,
)
from production_pulse_app.infrastructure.drivers.device_http_support import (
    parse_device_config_response,
)


def test_build_configure_http_payload_includes_ota_fields():
    body = build_configure_http_payload(
        {
            "wifiSsid": "Plant",
            "apiToken": "tok",
            "debounceMs": 100,
            "otaBaseUrl": "http://10.0.0.5/apps/production-pulse-api/",
            "branch": "01",
            "otaCheckIntervalMs": 60000,
        }
    )
    assert body["ssid"] == "Plant"
    assert body["apiToken"] == "tok"
    assert body["debounceMs"] == 100
    assert body["otaBaseUrl"] == "http://10.0.0.5/apps/production-pulse-api"
    assert body["branch"] == "01"
    assert body["otaCheckIntervalMs"] == 60000


def test_build_configure_http_payload_rejects_tiny_ota_interval():
    body = build_configure_http_payload({"otaCheckIntervalMs": 50})
    assert "otaCheckIntervalMs" not in body


def test_parse_device_config_response_includes_ota_without_secrets():
    parsed = parse_device_config_response(
        {
            "ssid": "Plant",
            "password": "secret",
            "apiToken": "secret",
            "otaBaseUrl": "http://10.0.0.5/apps/production-pulse-api",
            "branch": "01",
            "otaCheckIntervalMs": 60000,
            "apiTokenSet": True,
        }
    )
    assert parsed["otaBaseUrl"] == "http://10.0.0.5/apps/production-pulse-api"
    assert parsed["otaBaseUrlConfigured"] is True
    assert parsed["branch"] == "01"
    assert parsed["otaCheckIntervalMs"] == 60000
    assert "password" not in parsed
    assert "apiToken" not in parsed
