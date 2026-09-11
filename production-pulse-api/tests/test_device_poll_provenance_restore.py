from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_poll_service import DevicePollService
from production_pulse_app.domain.models.device_reading import DeviceReading
from production_pulse_app.domain.services.hardware_identity_types import (
    HardwareIdentityOutcome,
    HardwareResolutionResult,
)


def _same_hardware_mock() -> MagicMock:
    hw = MagicMock()
    assignment_id = uuid4()
    hw.resolve_for_poll.return_value = HardwareResolutionResult(
        outcome=HardwareIdentityOutcome.SAME_HARDWARE,
        assignment_id=assignment_id,
        hardware_unit_id=uuid4(),
        allow_counter_restore=True,
    )
    return hw


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
    devices.record_poll_success.side_effect = lambda _id, *, metrics, **_kwargs: {
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
    readings.insert.return_value = {
        "id": 9,
        "recorded_at": datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc),
    }
    readings.latest_recorded_at.return_value = None
    commands = MagicMock()
    commands.has_recent_successful_command.return_value = False
    rollups = MagicMock()

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        command_repository=commands,
        rollup_service=rollups,
        hardware_identity_service=_same_hardware_mock(),
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
    rollups.apply_persisted_reading.assert_called_once()


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
    devices.record_poll_success.side_effect = lambda _id, *, metrics, **_kwargs: {
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
    readings.insert.return_value = {
        "id": 10,
        "recorded_at": datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc),
    }
    readings.latest_recorded_at.return_value = None
    commands = MagicMock()
    commands.has_recent_successful_command.return_value = True
    rollups = MagicMock()

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        command_repository=commands,
        rollup_service=rollups,
        hardware_identity_service=_same_hardware_mock(),
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
    rollups.apply_persisted_reading.assert_called_once()


def test_poll_replacement_skips_hardware_set_and_preserves_logical():
    device_id = uuid4()
    devices = MagicMock()
    devices.get_by_id.return_value = {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "ip_address": "192.168.20.14",
        "last_metrics": {"counter": 138500, "counterRaw": 138500, "counterOffset": 0},
        "poll_interval_ms": 1000,
        "last_seen_at": None,
        "last_error": None,
        "enabled": True,
    }
    devices.record_poll_success.side_effect = lambda _id, *, metrics, **_kwargs: {
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
    readings.insert.return_value = {
        "id": 11,
        "recorded_at": datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc),
    }
    readings.latest_recorded_at.return_value = None
    commands = MagicMock()
    commands.has_recent_successful_command.return_value = False
    rollups = MagicMock()

    new_assignment = uuid4()
    hw = MagicMock()
    hw.resolve_for_poll.return_value = HardwareResolutionResult(
        outcome=HardwareIdentityOutcome.HARDWARE_REPLACEMENT,
        assignment_id=new_assignment,
        hardware_unit_id=uuid4(),
        previous_assignment_id=uuid4(),
        allow_counter_restore=False,
        replaced=True,
    )

    service = DevicePollService(
        device_repository=devices,
        binding_repository=bindings,
        reading_repository=readings,
        command_repository=commands,
        rollup_service=rollups,
        hardware_identity_service=hw,
    )
    driver = MagicMock()
    driver.read.return_value = DeviceReading(
        metrics={"counter": 0},
        meta={
            "hardwareUid": "ESP-BBBBBBBB",
            "controllerCode": "ESP-BBBBBBBB",
            "mac": "DD:EE:FF:44:55:66",
        },
    )
    service._registry = MagicMock()
    service._registry.build_capabilities.return_value = {"commands": [], "metrics": ["counter"]}
    service._registry.get_implementation.return_value = driver
    service._chip_health_from_driver = MagicMock(return_value={})

    payload = service.poll_and_persist(device_id, source="manual")

    assert payload["metrics"]["counter"] == 138500
    assert payload["meta"].get("hardware_replacement") is True
    driver.execute.assert_not_called()
    insert_kwargs = readings.insert.call_args.kwargs
    assert insert_kwargs["hardware_assignment_id"] == new_assignment
