from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    command_error_message,
    device_config_push_message,
    device_connectivity_codes,
    device_connectivity_http_status_code,
    device_connectivity_user_message,
    http_error_message,
    load_device_api_messages,
    validation_error_message,
)


def setup_function():
    load_device_api_messages.cache_clear()
    device_connectivity_codes.cache_clear()


def test_device_connectivity_codes_include_timeout_and_missing_ip():
    codes = device_connectivity_codes()
    assert "timeout" in codes
    assert "missing_ip" in codes
    assert "unauthorized" in codes
    assert "validation_error" not in codes


def test_device_connectivity_user_message_maps_timeout():
    message = device_connectivity_user_message("timeout")
    assert "não respondeu a tempo" in message.lower()


def test_device_connectivity_user_message_maps_unauthorized():
    message = device_connectivity_user_message("unauthorized")
    assert "token" in message.lower()


def test_device_connectivity_user_message_falls_back_to_driver_message():
    message = device_connectivity_user_message("unknown_code", fallback="Detalhe técnico do driver.")
    assert message == "Detalhe técnico do driver."


def test_device_connectivity_http_status_code_is_422():
    assert device_connectivity_http_status_code() == 422


def test_http_error_message_reads_not_found_device():
    message = http_error_message("notFoundDevice")
    assert "dispositivo" in message.lower()


def test_command_error_message_maps_unsupported_command():
    message = command_error_message("unsupported_command")
    assert "não suporta" in message.lower()


def test_validation_error_message_supports_placeholders():
    message = validation_error_message("poll_interval_out_of_range", min=1, max=300_000)
    assert "1" in message
    assert "300000" in message
    assert "milissegundos" in message.lower()


def test_device_config_push_message_unauthorized_is_specific():
    generic = device_config_push_message("failed")
    specific = device_config_push_message("failed", error_code="unauthorized")
    assert "token" in specific.lower()
    assert specific != generic


def test_device_config_push_message_skipped_pulse_only():
    message = device_config_push_message("skipped_pulse_only")
    assert "poll" in message.lower() or "não foi contactado" in message.lower()
