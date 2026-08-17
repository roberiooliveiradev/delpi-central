"""Streak de dias corridos sem ocorrência (NC, defeito, etc.)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def coerce_occurrence_date(value: Any) -> date | None:
    """Normaliza valor de ocorrência (date, datetime ou ISO) para ``date``."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def compute_occurrence_streak(
    occurrence_dates: list[Any],
    *,
    as_of: date,
    reference_start_date: date | None = None,
) -> dict[str, Any]:
    """
    Calcula streak a partir de datas de ocorrência distintas.

    - ``current_days_without_nc``: dias desde a última ocorrência até ``as_of``
      (ocorrência no próprio ``as_of`` → 0).
    - ``record_days_without_nc``: maior intervalo entre ocorrências consecutivas
      (diferença em dias) ou o streak atual, o que for maior.

    Sem ocorrências: usa ``reference_start_date`` como âncora; se também ausente,
    ambos ficam 0.
    """
    unique = sorted(
        {
            parsed
            for parsed in (coerce_occurrence_date(item) for item in occurrence_dates)
            if parsed is not None
        }
    )
    as_of_date = as_of
    reference = (
        reference_start_date
        if isinstance(reference_start_date, date)
        else None
    )

    if not unique:
        if reference is None:
            return {
                "current_days_without_nc": 0,
                "record_days_without_nc": 0,
                "last_nc_date": None,
                "reference_start_date": None,
                "as_of_date": as_of_date.isoformat(),
                "nc_count": 0,
            }
        current = max(0, (as_of_date - reference).days)
        return {
            "current_days_without_nc": current,
            "record_days_without_nc": current,
            "last_nc_date": None,
            "reference_start_date": reference.isoformat(),
            "as_of_date": as_of_date.isoformat(),
            "nc_count": 0,
        }

    last = unique[-1]
    current = max(0, (as_of_date - last).days)

    gaps: list[int] = []
    for previous, current_date in zip(unique, unique[1:]):
        gaps.append((current_date - previous).days)

    record = max([current, *gaps]) if gaps else current

    return {
        "current_days_without_nc": current,
        "record_days_without_nc": record,
        "last_nc_date": last.isoformat(),
        "reference_start_date": reference.isoformat() if reference else None,
        "as_of_date": as_of_date.isoformat(),
        "nc_count": len(unique),
    }
