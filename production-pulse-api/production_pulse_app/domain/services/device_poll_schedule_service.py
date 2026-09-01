from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_next_poll_at(
    poll_interval_seconds: int | float,
    *,
    now: datetime | None = None,
) -> datetime:
    base = max(0.5, min(300.0, float(poll_interval_seconds)))
    jitter_factor = random.uniform(0.9, 1.1)
    delay_seconds = base * jitter_factor
    current = utc_now() if now is None else now.astimezone(timezone.utc)
    return current + timedelta(seconds=delay_seconds)


def compute_initial_poll_at(
    poll_interval_seconds: int | float,
    *,
    now: datetime | None = None,
) -> datetime:
    base = max(0.5, min(300.0, float(poll_interval_seconds)))
    delay_seconds = random.uniform(0, float(base))
    current = utc_now() if now is None else now.astimezone(timezone.utc)
    return current + timedelta(seconds=delay_seconds)
