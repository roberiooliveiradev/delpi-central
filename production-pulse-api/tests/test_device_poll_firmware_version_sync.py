from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_poll_service import DevicePollService
from production_pulse_app.domain.models.device_reading import DeviceReading


def test_poll_and_persist_syncs_firmware_version_from_status_identity(monkeypatch):
    devices = MagicMock()
    bindings = MagicMock()
    readings = MagicMock()
    device_id = uuid4()
    device = {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "role_key": "pulse_counter",
        "last_metrics": {"counter": 1},
        "poll_interval_ms": 1000,
    }
    devices.get_by_id.return_value = device
    devices.record_poll_success.return_value = {
        **device,
        "installed_firmware_version": "esp8266_counter_v1.3.1",
    }
    bindings.get_active.return_value = {"id": uuid4()}
    readings.latest_recorded_at.return_value = None

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        firmware_job_service=MagicMock(),
        rollup_service=MagicMock(),
    )
    monkeypatch.setattr(service, "_has_recent_intentional_decrease", lambda *_a, **_k: False)
    monkeypatch.setattr(service, "_maybe_hardware_restore_counter", lambda *_a, **_k: None)
    monkeypatch.setattr(service, "_maybe_hardware_floor_counter", lambda *_a, **_k: None)
    monkeypatch.setattr(
        service,
        "_chip_health_from_driver",
        lambda _device: {"firmwareVersion": "esp8266_counter_v1.3.1"},
    )
    monkeypatch.setattr(service, "_capabilities", lambda *_a, **_k: {})
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.apply_monotonic_continuity",
        lambda **_k: ({"counter": 2}, {}),
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.compute_delta_metrics",
        lambda **_k: ({}, {}),
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.decide_persist_reading",
        lambda **_k: SimpleNamespace(should_persist=False, reason="test"),
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.public_metrics",
        lambda m: m if isinstance(m, dict) else {},
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.resolve_connectivity_status",
        lambda *_a, **_k: {"status": "online", "online": True, "graceSeconds": 0},
    )

    registry = MagicMock()
    driver = MagicMock()
    driver.read.return_value = DeviceReading(metrics={"counter": 2})
    registry.get_implementation.return_value = driver
    service._registry = registry

    service.poll_and_persist(device_id, source="scheduled")

    kwargs = devices.record_poll_success.call_args.kwargs
    assert kwargs["installed_firmware_version"] == "esp8266_counter_v1.3.1"
