import pytest

from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import validate_poll_interval


def test_validate_poll_interval_accepts_half_second():
    assert validate_poll_interval(0.5) == 0.5


def test_validate_poll_interval_rejects_below_minimum():
    with pytest.raises(DeviceValidationError):
        validate_poll_interval(0.49)


def test_validate_poll_interval_rounds_fractional_input():
    assert validate_poll_interval(1.234) == 1.23
