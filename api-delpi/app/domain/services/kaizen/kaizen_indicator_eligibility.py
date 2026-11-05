"""Elegibilidade de kaizen para indicadores de quantidade vs. ganhos financeiros.

- Quantidade (mês / período): status ``aprovado`` ou ``implantado``, âncora
  ``COALESCE(date_committee_approved, date_implemented)``.
- Ganhos financeiros: somente ``implantado`` (ver ``kaizen_savings_validity``).
- Existência no período (totais/situação/unidade do painel): âncora
  ``COALESCE(date_committee_approved, date_implemented, date_idea_received,
  created_at)`` — cadastros ainda sem marco de comitê/implantação (ex.:
  ``recebido``) pertencem ao período em que a ideia foi recebida/registrada.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

_QUANTITY_STATUSES = frozenset({"aprovado", "implantado"})
_IMPLEMENTED_STATUS = "implantado"


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return ""
    return (
        str(status)
        .strip()
        .lower()
        .replace("í", "i")
        .replace("ú", "u")
        .replace("ã", "a")
    )


def _as_date(value: Any) -> date | None:
    if value is None:
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


def counts_for_quantity(status: Optional[str]) -> bool:
    return _normalize_status(status) in _QUANTITY_STATUSES


def is_implemented_status(status: Optional[str]) -> bool:
    return _normalize_status(status) == _IMPLEMENTED_STATUS


def quantity_anchor_date(
    date_committee_approved: Any = None,
    date_implemented: Any = None,
) -> date | None:
    """Data que define o mês/período do indicador de quantidade."""
    return _as_date(date_committee_approved) or _as_date(date_implemented)


def quantity_anchor_from_row(row: dict[str, Any]) -> date | None:
    return quantity_anchor_date(
        row.get("date_committee_approved"),
        row.get("date_implemented"),
    )


def period_anchor_date(
    date_committee_approved: Any = None,
    date_implemented: Any = None,
    date_idea_received: Any = None,
    created_at: Any = None,
) -> date | None:
    """Data que situa o cadastro no recorte de período do painel.

    Marcos de aprovação/implantação primeiro; depois o recebimento da ideia;
    por fim a criação do registro (legado sem datas de ciclo de vida).
    """
    return (
        _as_date(date_committee_approved)
        or _as_date(date_implemented)
        or _as_date(date_idea_received)
        or _as_date(created_at)
    )


def period_anchor_from_row(row: dict[str, Any]) -> date | None:
    return period_anchor_date(
        row.get("date_committee_approved"),
        row.get("date_implemented"),
        row.get("date_idea_received"),
        row.get("created_at"),
    )


def date_in_range(
    day: date | None,
    range_start: date | None,
    range_end: date | None,
) -> bool:
    if day is None:
        return False
    if range_start is not None and day < range_start:
        return False
    if range_end is not None and day > range_end:
        return False
    return True
