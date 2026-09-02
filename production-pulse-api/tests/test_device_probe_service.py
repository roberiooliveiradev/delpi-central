from production_pulse_app.application.services.device_probe_service import DeviceProbeService
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    http_error_message,
)


def test_http_error_message_reads_catalog():
    assert "Dispositivo" in http_error_message("notFoundDevice")
    assert "Amarração" in http_error_message("notFoundBinding")


def test_probe_failure_payload_includes_user_message(monkeypatch):
    class _Driver:
        def test(self, _device):
            raise DeviceDriverError("timeout", technical_detail="HTTP timeout for test probe.")

    class _Registry:
        def get_implementation(self, _driver_key):
            return _Driver()

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_probe_service.get_device_driver_registry",
        lambda: _Registry(),
    )

    payload = DeviceProbeService()._run_probe(
        "esp8266_counter_v1",
        {"branch": "01", "ip_address": "192.168.20.2", "driver_key": "esp8266_counter_v1"},
    )

    assert payload["online"] is False
    assert payload["error"] == "timeout"
    assert "não respondeu a tempo" in payload["errorMessage"].lower()
    assert "timeout" not in payload["errorMessage"].lower()
