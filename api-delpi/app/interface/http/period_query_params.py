"""Query params de período HTTP — canônico `start_date`/`end_date` + aliases legado.

Dual-read durante transição (remoção planejada 2027-01). Precedente: `warehouse`/`location`.
Exclusões semânticas (não usar aqui): `issue_date_*`, `modified_*`, scheduling `from`/`to`.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Query

PERIOD_ALIAS_REMOVAL_DATE = "2027-01"

_CANONICAL_START_DESC = (
    "Period start date (YYYY-MM-DD). Canonical HTTP name; prefer this over legacy aliases."
)
_CANONICAL_END_DESC = (
    "Period end date (YYYY-MM-DD). Canonical HTTP name; prefer this over legacy aliases."
)
_LEGACY_START_DESC = (
    f"Legacy alias of start_date. Planned removal {PERIOD_ALIAS_REMOVAL_DATE}. Prefer start_date."
)
_LEGACY_END_DESC = (
    f"Legacy alias of end_date. Planned removal {PERIOD_ALIAS_REMOVAL_DATE}. Prefer end_date."
)

# Pares genéricos de período (não semânticos).
CANONICAL_PERIOD_PAIR = ("start_date", "end_date")
LEGACY_PERIOD_PAIRS: tuple[tuple[str, str], ...] = (
    ("date_start", "date_end"),
    ("dataInicio", "dataFim"),
    ("data_inicio", "data_fim"),
    ("date_from", "date_to"),
    ("data_inicial", "data_final"),
)
SEMANTIC_PERIOD_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("issue_date_start", "issue_date_end"),
        ("modified_from", "modified_to"),
        ("from", "to"),
    }
)


def _strip(value: Optional[str]) -> Optional[str]:
    # Chamada direta a handlers: default Query() é FieldInfo, não str.
    if value is None or not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def START_DATE_QUERY():
    return Query(
        None,
        description=_CANONICAL_START_DESC,
        json_schema_extra={"format": "date"},
    )


def END_DATE_QUERY():
    return Query(
        None,
        description=_CANONICAL_END_DESC,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATE_START_QUERY():
    return Query(
        None,
        description=_LEGACY_START_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATE_END_QUERY():
    return Query(
        None,
        description=_LEGACY_END_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_INICIO_QUERY():
    """HTTP name `dataInicio` (camelCase) — scrap/retrabalho legado."""
    return Query(
        None,
        alias="dataInicio",
        description=_LEGACY_START_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_FIM_QUERY():
    return Query(
        None,
        alias="dataFim",
        description=_LEGACY_END_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_INICIO_SNAKE_QUERY():
    return Query(
        None,
        description=_LEGACY_START_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_FIM_SNAKE_QUERY():
    return Query(
        None,
        description=_LEGACY_END_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATE_FROM_QUERY():
    return Query(
        None,
        description=_LEGACY_START_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATE_TO_QUERY():
    return Query(
        None,
        description=_LEGACY_END_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_INICIAL_QUERY():
    return Query(
        None,
        description=_LEGACY_START_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def LEGACY_DATA_FINAL_QUERY():
    return Query(
        None,
        description=_LEGACY_END_DESC,
        deprecated=True,
        json_schema_extra={"format": "date"},
    )


def resolve_period_dates(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    dataInicio: Optional[str] = None,
    dataFim: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    data_inicial: Optional[str] = None,
    data_final: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Dual-read: canônico vence; depois aliases legado na ordem documentada."""
    start = (
        _strip(start_date)
        or _strip(date_start)
        or _strip(dataInicio)
        or _strip(data_inicio)
        or _strip(date_from)
        or _strip(data_inicial)
    )
    end = (
        _strip(end_date)
        or _strip(date_end)
        or _strip(dataFim)
        or _strip(data_fim)
        or _strip(date_to)
        or _strip(data_final)
    )
    return start, end
