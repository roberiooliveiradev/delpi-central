import pytest

from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.services.device_command_payload_service import (
    normalize_set_command_payload,
)


def test_normalize_set_payload_accepts_counter():
    assert normalize_set_command_payload({"counter": 150}) == {"counter": 150}


def test_normalize_set_payload_accepts_contador_alias():
    assert normalize_set_command_payload({"contador": 12}) == {"counter": 12}


def test_normalize_set_payload_requires_value():
    with pytest.raises(DeviceValidationError) as exc_info:
        normalize_set_command_payload({})
    assert exc_info.value.code == "set_value_required"


def test_normalize_set_payload_rejects_negative():
    with pytest.raises(DeviceValidationError) as exc_info:
        normalize_set_command_payload({"counter": -1})
    assert exc_info.value.code == "set_value_out_of_range"
