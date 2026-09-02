from __future__ import annotations

from production_pulse_app.infrastructure.drivers.device_http_support import (
    device_auth_headers,
    parse_device_config_response,
    resolve_device_api_token,
)


def test_device_auth_headers_empty_without_token():
    assert device_auth_headers({"ip_address": "10.0.0.1"}) == {}
    assert device_auth_headers({"device_api_token": ""}) == {}
    assert device_auth_headers({"device_api_token": "   "}) == {}


def test_device_auth_headers_from_device_api_token():
    assert device_auth_headers({"device_api_token": "secret"}) == {"X-Device-Token": "secret"}


def test_device_auth_headers_from_api_token_alias():
    assert device_auth_headers({"apiToken": "alias-tok"}) == {"X-Device-Token": "alias-tok"}


def test_resolve_device_api_token_prefers_snake_column():
    assert resolve_device_api_token({"device_api_token": "a", "apiToken": "b"}) == "a"


def test_parse_device_config_response_strips_secrets():
    parsed = parse_device_config_response(
        {
            "ssid": "Plant",
            "password": "should-not-appear",
            "apiToken": "should-not-appear",
            "debounceMs": 150,
            "passwordSet": True,
            "apiTokenSet": True,
            "wifiConfigured": True,
        }
    )
    assert parsed == {
        "ssid": "Plant",
        "debounceMs": 150,
        "passwordSet": True,
        "apiTokenSet": True,
        "wifiConfigured": True,
    }
    assert "password" not in parsed
    assert "apiToken" not in parsed
