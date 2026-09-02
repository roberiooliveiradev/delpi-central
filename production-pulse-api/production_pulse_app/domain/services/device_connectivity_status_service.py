from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from production_pulse_app.config import settings


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def grace_seconds_for_device(device: dict[str, Any]) -> int:
    interval_ms = float(device.get("poll_interval_ms") or 30_000)
    interval_seconds = interval_ms / 1000.0
    raw = interval_seconds * settings.PP_ONLINE_GRACE_MULTIPLIER
    return int(
        max(
            settings.PP_ONLINE_GRACE_MIN_SECONDS,
            min(settings.PP_ONLINE_GRACE_MAX_SECONDS, raw),
        )
    )


def resolve_connectivity_status(
    device: dict[str, Any],
    *,
    has_binding: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _utc_now() if now is None else _as_utc(now)

    if not device.get("enabled", True):
        return {"status": "disabled", "online": False, "graceSeconds": grace_seconds_for_device(device)}

    if not has_binding:
        return {"status": "no_binding", "online": False, "graceSeconds": grace_seconds_for_device(device)}

    last_seen = device.get("last_seen_at")
    grace = grace_seconds_for_device(device)
    if last_seen is None:
        return {"status": "offline", "online": False, "graceSeconds": grace}

    elapsed = (current - _as_utc(last_seen)).total_seconds()
    online = elapsed <= grace
    return {
        "status": "online" if online else "offline",
        "online": online,
        "graceSeconds": grace,
    }
