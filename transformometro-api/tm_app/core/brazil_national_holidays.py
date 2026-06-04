"""Feriados nacionais fixos e móveis (Brasil) para cálculo de dias úteis."""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def easter_sunday(year: int) -> date:
    """Domingo de Páscoa (calendário gregoriano)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


@lru_cache(maxsize=64)
def brazil_national_holidays(year: int) -> frozenset[date]:
    """Feriados nacionais segundo calendário federal (fixos + móveis ligados à Páscoa)."""
    easter = easter_sunday(year)
    return frozenset(
        {
            date(year, 1, 1),
            date(year, 4, 21),
            date(year, 5, 1),
            date(year, 9, 7),
            date(year, 10, 12),
            date(year, 11, 2),
            date(year, 11, 15),
            date(year, 12, 25),
            easter - timedelta(days=48),
            easter - timedelta(days=47),
            easter - timedelta(days=2),
            easter + timedelta(days=60),
        }
    )


def is_national_holiday(value: date) -> bool:
    return value in brazil_national_holidays(value.year)
