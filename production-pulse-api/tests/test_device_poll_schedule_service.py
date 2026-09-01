from datetime import datetime, timedelta, timezone

from production_pulse_app.domain.services.device_poll_schedule_service import (
    compute_initial_poll_at,
    compute_next_poll_at,
)


def test_next_poll_at_applies_jitter_bounds():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = [compute_next_poll_at(100, now=now) for _ in range(50)]
    deltas = [(sample - now).total_seconds() for sample in samples]
    assert all(90 <= delta <= 110 for delta in deltas)


def test_initial_poll_at_within_interval():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    samples = [compute_initial_poll_at(60, now=now) for _ in range(20)]
    for sample in samples:
        delta = (sample - now).total_seconds()
        assert 0 <= delta <= 60
