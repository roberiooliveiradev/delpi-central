"""Cálculo de dias sem NC em LMP (streak atual e recorde)."""

from __future__ import annotations

from datetime import date
from typing import Any


def compute_lmp_nc_streak(
    occurrence_dates: list[date],
    *,
    as_of: date,
) -> dict[str, Any]:
    """
    Calcula streak a partir das datas de ocorrência (``registered_at`` por dia).

    - ``current_days_without_nc``: dias desde a última NC até ``as_of``
      (NC no próprio ``as_of`` → 0).
    - ``record_days_without_nc``: maior intervalo entre NCs consecutivas
      (diferença em dias) ou o streak atual, o que for maior.

    Sem NCs: ambos 0 e ``last_nc_date`` nulo.
    """
    unique = sorted({d for d in occurrence_dates if isinstance(d, date)})
    as_of_date = as_of

    if not unique:
        return {
            "current_days_without_nc": 0,
            "record_days_without_nc": 0,
            "last_nc_date": None,
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
        "as_of_date": as_of_date.isoformat(),
        "nc_count": len(unique),
    }
