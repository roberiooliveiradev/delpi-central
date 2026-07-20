"""Dias úteis (segunda a sexta) — sem descontar feriados."""

from __future__ import annotations

from datetime import date, timedelta


class SafetyStockBusinessDaysService:
    """Contagem inclusiva de dias úteis para análise de consumo/lead time."""

    @staticmethod
    def is_business_day(value: date) -> bool:
        return value.weekday() < 5

    @classmethod
    def count_inclusive(cls, start: date, end: date) -> int:
        if end < start:
            return 0

        total_days = (end - start).days + 1
        full_weeks, remaining = divmod(total_days, 7)
        count = full_weeks * 5

        cursor = start + timedelta(days=full_weeks * 7)
        for _ in range(remaining):
            if cls.is_business_day(cursor):
                count += 1
            cursor += timedelta(days=1)

        return count

    @classmethod
    def count_in_calendar_span(cls, calendar_days: int, *, start: date | None = None) -> int:
        """Quantos dias úteis cabem em N dias corridos a partir de ``start`` (inclusivo)."""
        days = int(calendar_days or 0)
        if days <= 0:
            return 0
        origin = start or date.today()
        end = origin + timedelta(days=days - 1)
        return cls.count_inclusive(origin, end)
