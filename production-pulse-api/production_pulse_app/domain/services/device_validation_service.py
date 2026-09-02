from __future__ import annotations

from dataclasses import dataclass

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    matches_ipv4,
    name_max_length,
    poll_interval_max,
    poll_interval_min,
    valid_branches,
)


@dataclass(frozen=True)
class ResolvedDriver:
    driver_key: str
    role_key: str


def resolve_driver(driver_key: str) -> ResolvedDriver:
    resolved = get_device_driver_registry().resolve_driver(driver_key)
    return ResolvedDriver(driver_key=resolved.driver_key, role_key=resolved.role_key)


def validate_branch(branch: str) -> str:
    normalized = (branch or "").strip()
    if not normalized:
        raise DeviceValidationError("branch_required")
    if normalized not in valid_branches():
        raise DeviceValidationError("invalid_branch")
    return normalized


def validate_poll_interval_ms(milliseconds: int | float) -> int:
    minimum = poll_interval_min()
    maximum = poll_interval_max()
    value = int(round(float(milliseconds)))
    if value < minimum or value > maximum:
        raise DeviceValidationError(
            "poll_interval_out_of_range",
            min=minimum,
            max=maximum,
        )
    return value


def normalize_ip_address(ip_address: str) -> str:
    normalized = (ip_address or "").strip()
    if not normalized:
        raise DeviceValidationError("ip_address_required")
    if not matches_ipv4(normalized):
        raise DeviceValidationError("invalid_ipv4")
    return normalized


def normalize_name(name: str) -> str:
    normalized = (name or "").strip()
    if not normalized:
        raise DeviceValidationError("name_required")
    if len(normalized) > name_max_length():
        raise DeviceValidationError("name_too_long")
    return normalized


__all__ = [
    "DeviceValidationError",
    "ResolvedDriver",
    "resolve_driver",
    "validate_branch",
    "validate_poll_interval_ms",
    "normalize_ip_address",
    "normalize_name",
]
