from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_poll_service import DevicePollService
from production_pulse_app.domain.models.device_reading import DeviceReading


def test_poll_restores_small_drop_without_recent_command():
    device_id = uuid4()
    devices = MagicMock()
    devices.get_by_id.return_value = {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "last_metrics": {"counter": 30, "counterRaw": 30, "counterOffset": 0},
        "poll_interval_ms": 1000,
        "last_seen_at": None,
        "last_error": None,
        "enabled": True,
    }
    devices.record_poll_success.side_effect = lambda _id, *, metrics: {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "last_metrics": metrics,
        "poll_interval_ms": 1000,
        "last_seen_at": None,
        "last_error": None,
        "enabled": True,
    }
    bindings = MagicMock()
    bindings.get_active.return_value = {"id": 1}
    readings = MagicMock()
    readings.insert.return_value = {"id": 9, "recorded_at": "2026-09-02T14:00:00+00:00"}
    readings.latest_recorded_at.return_value = None
    commands = MagicMock()
    commands.has_recent_successful_command.return_value = False

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        command_repository=commands,
    )
    driver = MagicMock()
    driver.read.return_value = DeviceReading(metrics={"counter": 0})
    driver.execute.return_value = MagicMock(
        success=True,
        metrics={"counter": 30},
    )
    service._registry = MagicMock()
    service._registry.build_capabilities.return_value = {"commands": [], "metrics": ["counter"]}
    service._registry.get_implementation.return_value = driver
    service._chip_health_from_driver = MagicMock(return_value={})

    payload = service.poll_and_persist(device_id, source="manual")

    assert payload["metrics"]["counter"] == 30
    assert payload["meta"]["counter_restored"] is True
    assert payload["meta"]["counter_restore_reason"] == "unexplained_drop"
    driver.execute.assert_called_once()
    assert driver.execute.call_args.args[1] == "set"
    assert driver.execute.call_args.kwargs["payload"] == {"counter": 30}


def test_poll_accepts_drop_when_recent_decrement_command():
    device_id = uuid4()
    devices = MagicMock()
    devices.get_by_id.return_value = {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "last_metrics": {"counter": 30, "counterRaw": 30, "counterOffset": 0},
        "poll_interval_ms": 1000,
        "last_seen_at": None,
        "last_error": None,
        "enabled": True,
    }
    devices.record_poll_success.side_effect = lambda _id, *, metrics: {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "last_metrics": metrics,
        "poll_interval_ms": 1000,
        "last_seen_at": None,
        "last_error": None,
        "enabled": True,
    }
    bindings = MagicMock()
    bindings.get_active.return_value = {"id": 1}
    readings = MagicMock()
    readings.insert.return_value = {"id": 10, "recorded_at": "2026-09-02T14:00:00+00:00"}
    readings.latest_recorded_at.return_value = None
    commands = MagicMock()
    commands.has_recent_successful_command.return_value = True

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        command_repository=commands,
    )
    driver = MagicMock()
    driver.read.return_value = DeviceReading(metrics={"counter": 29})
    service._registry = MagicMock()
    service._registry.build_capabilities.return_value = {"commands": [], "metrics": ["counter"]}
    service._registry.get_implementation.return_value = driver
    service._chip_health_from_driver = MagicMock(return_value={})

    payload = service.poll_and_persist(device_id, source="manual")

    assert payload["metrics"]["counter"] == 29
    assert payload["meta"].get("counter_decrease_accepted") is True
    assert "counter_restored" not in payload["meta"]
    driver.execute.assert_not_called()
