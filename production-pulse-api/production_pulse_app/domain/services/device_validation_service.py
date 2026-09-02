from __future__ import annotations

from dataclasses import dataclass

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import DeviceValidationError

POLL_INTERVAL_MIN = 0.5
POLL_INTERVAL_MAX = 300.0
VALID_BRANCHES = frozenset({"01", "02"})


@dataclass(frozen=True)
class ResolvedDriver:
    driver_key: str
    role_key: str


def resolve_driver(driver_key: str) -> ResolvedDriver:
    resolved = get_device_driver_registry().resolve_driver(driver_key)
    return ResolvedDriver(driver_key=resolved.driver_key, role_key=resolved.role_key)


def validate_branch(branch: str) -> str:
    normalized = (branch or "").strip()
    if normalized not in VALID_BRANCHES:
        raise DeviceValidationError("invalid_branch")
    return normalized


def validate_poll_interval(seconds: int | float) -> float:
    value = float(seconds)
    if value < POLL_INTERVAL_MIN or value > POLL_INTERVAL_MAX:
        raise DeviceValidationError(
            "poll_interval_out_of_range",
            min=POLL_INTERVAL_MIN,
            max=int(POLL_INTERVAL_MAX),
        )
    return round(value, 2)


def normalize_ip_address(ip_address: str) -> str:
    normalized = (ip_address or "").strip()
    if not normalized:
        raise DeviceValidationError("ip_address_required")
    return normalized


def normalize_name(name: str) -> str:
    normalized = (name or "").strip()
    if not normalized:
        raise DeviceValidationError("name_required")
    if len(normalized) > 120:
        raise DeviceValidationError("name_too_long")
    return normalized


__all__ = [
    "DeviceValidationError",
    "ResolvedDriver",
    "resolve_driver",
    "validate_branch",
    "validate_poll_interval",
    "normalize_ip_address",
    "normalize_name",
]
