import pytest

from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import validate_poll_interval_ms


def test_validate_poll_interval_ms_accepts_minimum():
    assert validate_poll_interval_ms(500) == 500


def test_validate_poll_interval_ms_rejects_below_minimum():
    with pytest.raises(DeviceValidationError):
        validate_poll_interval_ms(499)


def test_validate_poll_interval_ms_rounds_fractional_input():
    assert validate_poll_interval_ms(1234.6) == 1235
