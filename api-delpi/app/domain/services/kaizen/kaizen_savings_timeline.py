"""Ganho por período a partir das melhorias (revisões) de um kaizen.

Cada melhoria (revisão) tem vigência própria (`effective_from`/`effective_until`)
e contabiliza sua economia por **1 ano a partir de `effective_from`** (regra de
aniversário — ver `kaizen_savings_validity`). O ganho de um período é a soma, por
melhoria, de `daily_savings × dias ativos` dentro do período, respeitando:

  * o fim da vigência (`effective_until` — quando outra melhoria assumiu), e
  * o teto de 1 ano da própria melhoria (`savings_valid_until`).

Como as vigências são sequenciais (uma melhoria fecha a anterior), no máximo uma
melhoria está ativa em cada instante; lançar uma nova melhoria "renova" o
aniversário do kaizen.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Optional

from app.domain.services.kaizen import kaizen_savings_validity


def _as_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# Status de versão que já esteve implantada e, portanto, contabiliza economia no período.
_COUNTED_VERSION_STATUS = {"implantado", "substituido", "descontinuado"}


def _version_counts(revision: dict[str, Any]) -> bool:
    """Rascunhos (recebido) e cancelados nunca somam no ganho por período."""
    status = revision.get("version_status")
    if status is None:
        return True  # compat: revisões antigas sem status são tratadas como implantadas
    return status in _COUNTED_VERSION_STATUS


def revision_last_active_day(
    effective_from: Optional[date],
    effective_until: Optional[date],
    *,
    today: Optional[date] = None,
) -> Optional[date]:
    """Último dia em que a melhoria contabiliza (menor entre fim de vigência e teto de 1 ano)."""
    if effective_from is None:
        return None
    reference_today = today or date.today()
    valid_until = kaizen_savings_validity.savings_valid_until(effective_from)
    candidates = [valid_until]
    if effective_until is not None:
        # A melhoria seguinte assumiu em effective_until; conta até o dia anterior.
        candidates.append(effective_until - timedelta(days=1))
    else:
        candidates.append(reference_today)
    return min(candidates)


def revision_active_days_in_range(
    effective_from: Optional[date],
    effective_until: Optional[date],
    range_start: Optional[date],
    range_end: Optional[date],
    *,
    today: Optional[date] = None,
) -> int:
    if effective_from is None:
        return 0
    reference_today = today or date.today()
    last_day = revision_last_active_day(effective_from, effective_until, today=reference_today)
    if last_day is None:
        return 0
    start = max(effective_from, range_start or effective_from)
    # Cap explícito em ``today``: mesmo com range_end futuro, não projeta ganho.
    end = min(last_day, range_end or reference_today, reference_today)
    if start > end:
        return 0
    return (end - start).days + 1


def period_savings(
    revisions: Iterable[dict[str, Any]],
    range_start: Optional[date] = None,
    range_end: Optional[date] = None,
    *,
    today: Optional[date] = None,
) -> float:
    """Ganho total do período somando cada melhoria dentro da sua validade."""
    total = 0.0
    for revision in revisions:
        if not _version_counts(revision):
            continue
        daily = _as_float(revision.get("daily_savings"))
        if not daily:
            continue
        active_days = revision_active_days_in_range(
            _as_date(revision.get("effective_from")),
            _as_date(revision.get("effective_until")),
            range_start,
            range_end,
            today=today,
        )
        total += daily * active_days
    return round(total, 2)


def current_active_savings(
    revisions: Iterable[dict[str, Any]],
    *,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """Economia vigente hoje: a melhoria ativa (se houver) dentro da validade de 1 ano."""
    reference_today = today or date.today()
    for revision in revisions:
        if revision.get("version_status") not in (None, "implantado"):
            continue
        effective_from = _as_date(revision.get("effective_from"))
        effective_until = _as_date(revision.get("effective_until"))
        if effective_from is None or effective_from > reference_today:
            continue
        last_day = revision_last_active_day(effective_from, effective_until, today=reference_today)
        if last_day is not None and reference_today <= last_day:
            return {
                "revision_number": revision.get("revision_number"),
                "daily_savings": _as_float(revision.get("daily_savings")),
                "annual_savings": _as_float(revision.get("annual_savings")),
                "valid_until": kaizen_savings_validity.savings_valid_until(effective_from),
                "active": True,
            }
    return {
        "revision_number": None,
        "daily_savings": None,
        "annual_savings": None,
        "valid_until": None,
        "active": False,
    }
