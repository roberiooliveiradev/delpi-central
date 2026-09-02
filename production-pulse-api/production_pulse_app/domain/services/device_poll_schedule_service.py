from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from production_pulse_app.infrastructure.content.device_validation_content_service import (
    poll_interval_max,
    poll_interval_min,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clamp_poll_interval_ms(poll_interval_ms: int | float) -> int:
    return max(poll_interval_min(), min(poll_interval_max(), int(round(float(poll_interval_ms)))))


def compute_next_poll_at(
    poll_interval_ms: int | float,
    *,
    now: datetime | None = None,
) -> datetime:
    base_ms = _clamp_poll_interval_ms(poll_interval_ms)
    jitter_factor = random.uniform(0.9, 1.1)
    delay_ms = base_ms * jitter_factor
    current = utc_now() if now is None else now.astimezone(timezone.utc)
    return current + timedelta(milliseconds=delay_ms)


def compute_initial_poll_at(
    poll_interval_ms: int | float,
    *,
    now: datetime | None = None,
) -> datetime:
    base_ms = _clamp_poll_interval_ms(poll_interval_ms)
    delay_ms = random.uniform(0, float(base_ms))
    current = utc_now() if now is None else now.astimezone(timezone.utc)
    return current + timedelta(milliseconds=delay_ms)
