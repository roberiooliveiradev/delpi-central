"""Média diária de volume — só dias úteis (seg–sex).

Finais de semana podem aparecer na série do gráfico/total, mas não entram no
denominador nem no numerador da média de produção diária do PCP.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _parse_iso_date(raw: Any) -> date | None:
    text = str(raw or "").strip()
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def is_weekend(day: date) -> bool:
    """Sábado (5) ou domingo (6) no calendário civil."""
    return day.weekday() >= 5


def weekday_daily_average(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Média dos pontos com data em dia útil.

    Retorna ``average``, ``weekday_day_count`` e ``weekday_total``. Sem dia útil
    com valor → ``average`` nulo e contagens zeradas.
    """
    weekday_total = 0.0
    weekday_day_count = 0
    for point in points:
        day = _parse_iso_date(point.get("start_date"))
        if day is None or is_weekend(day):
            continue
        try:
            value = float(point.get("value"))
        except (TypeError, ValueError):
            continue
        if value != value:  # NaN
            continue
        weekday_total += value
        weekday_day_count += 1

    if weekday_day_count == 0:
        return {
            "average": None,
            "weekday_day_count": 0,
            "weekday_total": 0.0,
        }

    return {
        "average": round(weekday_total / weekday_day_count, 6),
        "weekday_day_count": weekday_day_count,
        "weekday_total": round(weekday_total, 6),
    }
