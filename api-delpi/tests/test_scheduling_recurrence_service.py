"""Testes do serviço de expansão de recorrência de agendamento."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.domain.services.scheduling_recurrence_service import (
    RecurrenceValidationError,
    expand_recurrence_slots,
)


def _dt(year: int, month: int, day: int, hour: int = 10) -> datetime:
    return datetime(year, month, day, hour, 0, tzinfo=timezone.utc)


def test_expand_weekly_slots() -> None:
    slots = expand_recurrence_slots(
        start_at=_dt(2026, 6, 3),
        end_at=_dt(2026, 6, 3, 11),
        frequency="weekly",
        until=_dt(2026, 6, 24),
    )
    assert len(slots) == 4
    assert slots[0][0] == _dt(2026, 6, 3)
    assert slots[1][0] == _dt(2026, 6, 10)
    assert slots[3][0] == _dt(2026, 6, 24)
    duration = slots[0][1] - slots[0][0]
    assert all((end - start) == duration for start, end in slots)


def test_expand_monthly_slots_handles_short_months() -> None:
    slots = expand_recurrence_slots(
        start_at=_dt(2026, 1, 31),
        end_at=_dt(2026, 1, 31, 11),
        frequency="monthly",
        until=_dt(2026, 4, 30),
    )
    assert len(slots) == 4
    assert slots[0][0].day == 31
    assert slots[1][0] == _dt(2026, 2, 28)
    assert slots[2][0] == _dt(2026, 3, 31)


def test_expand_rejects_until_before_start() -> None:
    with pytest.raises(RecurrenceValidationError):
        expand_recurrence_slots(
            start_at=_dt(2026, 6, 10),
            end_at=_dt(2026, 6, 10, 11),
            frequency="weekly",
            until=_dt(2026, 6, 3),
        )
