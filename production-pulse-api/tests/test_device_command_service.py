from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_command_service import DeviceCommandService
from production_pulse_app.domain.errors import CommandNotSupportedError
from production_pulse_app.domain.models.device_reading import CommandResult
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    command_error_message,
)


def test_unsupported_command_raises_coded_error():
    service = DeviceCommandService(
        device_repository=MagicMock(),
        command_repository=MagicMock(),
        reading_repository=MagicMock(),
    )
    service._devices.get_by_id.return_value = {
        "id": uuid4(),
        "driver_key": "esp8266_gauge_v1",
        "last_metrics": {},
    }

    try:
        service.execute_command(uuid4(), "reset", actor_sub="tester")
    except CommandNotSupportedError as exc:
        assert exc.code == "unsupported_command"
    else:
        raise AssertionError("expected CommandNotSupportedError")


def test_resolve_command_error_message_uses_json_catalog():
    message = DeviceCommandService._resolve_command_error_message(
        CommandResult(success=False, error_code="unsupported_command")
    )
    assert message == command_error_message("unsupported_command")


def test_decrement_floors_negative_and_syncs_hardware():
    device_id = uuid4()
    devices = MagicMock()
    devices.get_by_id.return_value = {
        "id": device_id,
        "driver_key": "esp8266_counter_v1",
        "last_metrics": {"counter": 0, "counterRaw": 0, "counterOffset": 0},
    }
    commands = MagicMock()
    commands.insert.return_value = {"id": uuid4()}
    readings = MagicMock()
    readings.insert.return_value = {"id": 1}

    service = DeviceCommandService(
        device_repository=devices,
        command_repository=commands,
        reading_repository=readings,
    )
    driver = MagicMock()
    driver.execute.side_effect = [
        CommandResult(success=True, metrics={"counter": -3}, response_payload={"contador": -3}),
        CommandResult(success=True, metrics={"counter": 0}, response_payload={"contador": 0}),
    ]
    service._registry = MagicMock()
    service._registry.build_capabilities.return_value = {
        "commands": ["increment", "decrement", "reset", "set"],
    }
    service._registry.get_implementation.return_value = driver

    result = service.execute_command(device_id, "decrement", actor_sub="tester")

    assert result["success"] is True
    assert result["metrics"] == {"counter": 0}
    assert driver.execute.call_count == 2
    assert driver.execute.call_args_list[1].args[1] == "set"
    assert driver.execute.call_args_list[1].kwargs["payload"] == {"counter": 0}
    devices.record_poll_success.assert_called_once()
    persisted = devices.record_poll_success.call_args.kwargs["metrics"]
    assert persisted["counter"] == 0
