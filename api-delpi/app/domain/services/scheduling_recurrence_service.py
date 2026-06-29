from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from typing import Literal

RecurrenceFrequency = Literal["weekly", "monthly"]

MAX_WEEKLY_OCCURRENCES = 52
MAX_MONTHLY_OCCURRENCES = 24


class RecurrenceValidationError(ValueError):
    """Parâmetros de recorrência inválidos."""


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def expand_recurrence_slots(
    *,
    start_at: datetime,
    end_at: datetime,
    frequency: RecurrenceFrequency,
    until: datetime,
    interval: int = 1,
) -> list[tuple[datetime, datetime]]:
    """Gera pares (início, término) para cada ocorrência da série."""
    start_at = _ensure_aware(start_at)
    end_at = _ensure_aware(end_at)
    until = _ensure_aware(until)

    if end_at <= start_at:
        raise RecurrenceValidationError("O horário de término deve ser posterior ao início.")
    if until < start_at:
        raise RecurrenceValidationError("A data final da recorrência deve ser igual ou posterior ao início.")
    if interval < 1:
        raise RecurrenceValidationError("O intervalo da recorrência deve ser pelo menos 1.")

    duration = end_at - start_at
    max_count = MAX_WEEKLY_OCCURRENCES if frequency == "weekly" else MAX_MONTHLY_OCCURRENCES
    slots: list[tuple[datetime, datetime]] = []
    current_start = start_at

    while current_start <= until and len(slots) < max_count:
        current_end = current_start + duration
        slots.append((current_start, current_end))
        if frequency == "weekly":
            current_start = current_start + timedelta(weeks=interval)
        else:
            current_start = _add_months(current_start, interval)

    if not slots:
        raise RecurrenceValidationError("Nenhuma ocorrência gerada para o período informado.")

    return slots
