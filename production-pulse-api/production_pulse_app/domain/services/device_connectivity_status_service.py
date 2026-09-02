from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from production_pulse_app.config import settings
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    online_grace_max_ms,
    online_grace_min_ms,
    online_grace_multiplier,
    poll_interval_default,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _grace_multiplier() -> int:
    if settings.PP_ONLINE_GRACE_MULTIPLIER is not None:
        return max(1, settings.PP_ONLINE_GRACE_MULTIPLIER)
    return online_grace_multiplier()


def _grace_min_ms() -> int:
    if settings.PP_ONLINE_GRACE_MIN_SECONDS is not None:
        return max(1, settings.PP_ONLINE_GRACE_MIN_SECONDS * 1000)
    return online_grace_min_ms()


def _grace_max_ms() -> int:
    if settings.PP_ONLINE_GRACE_MAX_SECONDS is not None:
        return max(1, settings.PP_ONLINE_GRACE_MAX_SECONDS * 1000)
    return online_grace_max_ms()


def grace_ms_for_device(device: dict[str, Any]) -> int:
    """Grace window canônica: clamp(poll_interval_ms × multiplier, min, max)."""
    interval_ms = float(device.get("poll_interval_ms") or poll_interval_default())
    raw = interval_ms * _grace_multiplier()
    return int(max(_grace_min_ms(), min(_grace_max_ms(), round(raw))))


def grace_seconds_for_device(device: dict[str, Any]) -> int:
    return max(1, int(round(grace_ms_for_device(device) / 1000.0)))


def resolve_connectivity_status(
    device: dict[str, Any],
    *,
    has_binding: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _utc_now() if now is None else _as_utc(now)
    grace_ms = grace_ms_for_device(device)
    grace_seconds = max(1, int(round(grace_ms / 1000.0)))

    if not device.get("enabled", True):
        return {"status": "disabled", "online": False, "graceSeconds": grace_seconds, "graceMs": grace_ms}

    if not has_binding:
        return {"status": "no_binding", "online": False, "graceSeconds": grace_seconds, "graceMs": grace_ms}

    last_seen = device.get("last_seen_at")
    if last_seen is None:
        return {"status": "offline", "online": False, "graceSeconds": grace_seconds, "graceMs": grace_ms}

    elapsed_ms = (current - _as_utc(last_seen)).total_seconds() * 1000.0
    online = elapsed_ms <= grace_ms
    return {
        "status": "online" if online else "offline",
        "online": online,
        "graceSeconds": grace_seconds,
        "graceMs": grace_ms,
    }
