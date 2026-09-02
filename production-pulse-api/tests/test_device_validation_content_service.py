from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import (
    normalize_ip_address,
    normalize_name,
    validate_branch,
    validate_poll_interval_ms,
)
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    load_device_validation_content,
    matches_ipv4,
    name_max_length,
    poll_interval_default,
    poll_interval_max,
    poll_interval_min,
    valid_branches,
)


def test_load_device_validation_content_has_poll_limits():
    content = load_device_validation_content()
    assert content["limits"]["pollIntervalMs"]["min"] == 500
    assert content["limits"]["pollIntervalMs"]["max"] == 300_000
    assert content["limits"]["pollIntervalMs"]["default"] == 30_000


def test_poll_interval_limits_match_json():
    assert poll_interval_min() == 500
    assert poll_interval_max() == 300_000
    assert poll_interval_default() == 30_000


def test_valid_branches_include_01_and_02():
    assert valid_branches() == frozenset({"01", "02"})


def test_matches_ipv4_accepts_private_address():
    assert matches_ipv4("192.168.20.2")


def test_matches_ipv4_rejects_invalid_octets():
    assert not matches_ipv4("999.1.1.1")


def test_validate_poll_interval_ms_accepts_minimum():
    assert validate_poll_interval_ms(500) == 500


def test_validate_poll_interval_ms_rejects_below_minimum():
    try:
        validate_poll_interval_ms(400)
    except DeviceValidationError as exc:
        assert exc.code == "poll_interval_out_of_range"
        assert exc.params["min"] == 500
        assert exc.params["max"] == 300_000
    else:
        raise AssertionError("expected DeviceValidationError")


def test_normalize_ip_address_rejects_invalid_ipv4():
    try:
        normalize_ip_address("999.1.1.1")
    except DeviceValidationError as exc:
        assert exc.code == "invalid_ipv4"
    else:
        raise AssertionError("expected DeviceValidationError")


def test_normalize_name_rejects_long_value():
    try:
        normalize_name("x" * (name_max_length() + 1))
    except DeviceValidationError as exc:
        assert exc.code == "name_too_long"
    else:
        raise AssertionError("expected DeviceValidationError")


def test_validate_branch_requires_value():
    try:
        validate_branch("")
    except DeviceValidationError as exc:
        assert exc.code == "branch_required"
    else:
        raise AssertionError("expected DeviceValidationError")
