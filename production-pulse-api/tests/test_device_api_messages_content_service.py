from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    device_connectivity_codes,
    device_connectivity_http_status_code,
    device_connectivity_user_message,
)


def test_device_connectivity_codes_include_timeout_and_missing_ip():
    codes = device_connectivity_codes()
    assert "timeout" in codes
    assert "missing_ip" in codes
    assert "validation_error" not in codes


def test_device_connectivity_user_message_maps_timeout():
    message = device_connectivity_user_message("timeout")
    assert "não respondeu a tempo" in message.lower()


def test_device_connectivity_user_message_falls_back_to_driver_message():
    message = device_connectivity_user_message("unknown_code", fallback="Detalhe técnico do driver.")
    assert message == "Detalhe técnico do driver."


def test_device_connectivity_http_status_code_is_422():
    assert device_connectivity_http_status_code() == 422
