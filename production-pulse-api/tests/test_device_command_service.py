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
