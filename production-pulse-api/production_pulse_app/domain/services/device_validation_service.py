from __future__ import annotations

from dataclasses import dataclass

# Stub até E3.S0 (device_drivers.json). driver_key → role_key.
DRIVER_ROLE_MAP: dict[str, str] = {
    "esp8266_counter_v1": "pulse_counter",
    "esp8266_gauge_v1": "process_gauge",
}

POLL_INTERVAL_MIN = 5
POLL_INTERVAL_MAX = 300
VALID_BRANCHES = frozenset({"01", "02"})


class DeviceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedDriver:
    driver_key: str
    role_key: str


def resolve_driver(driver_key: str) -> ResolvedDriver:
    normalized = (driver_key or "").strip()
    if not normalized:
        raise DeviceValidationError("driver_key é obrigatório.")
    role_key = DRIVER_ROLE_MAP.get(normalized)
    if role_key is None:
        raise DeviceValidationError(f"Driver desconhecido: {normalized}")
    return ResolvedDriver(driver_key=normalized, role_key=role_key)


def validate_branch(branch: str) -> str:
    normalized = (branch or "").strip()
    if normalized not in VALID_BRANCHES:
        raise DeviceValidationError("branch deve ser 01 ou 02.")
    return normalized


def validate_poll_interval(seconds: int) -> int:
    if seconds < POLL_INTERVAL_MIN or seconds > POLL_INTERVAL_MAX:
        raise DeviceValidationError(
            f"poll_interval_seconds deve estar entre {POLL_INTERVAL_MIN} e {POLL_INTERVAL_MAX}."
        )
    return seconds


def normalize_ip_address(ip_address: str) -> str:
    normalized = (ip_address or "").strip()
    if not normalized:
        raise DeviceValidationError("ip_address é obrigatório.")
    return normalized


def normalize_name(name: str) -> str:
    normalized = (name or "").strip()
    if not normalized:
        raise DeviceValidationError("name é obrigatório.")
    if len(normalized) > 120:
        raise DeviceValidationError("name deve ter no máximo 120 caracteres.")
    return normalized
