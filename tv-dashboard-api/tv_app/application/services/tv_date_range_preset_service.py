"""Presets relativos de período para fontes TV (datas sempre recalculadas no fetch)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

DATE_RANGE_PRESET_KEY = "dateRangePreset"
PERIOD_DAYS_KEY = "periodDays"

START_KEYS = (
    "date_start",
    "start_date",
    "date_from",
    "dataInicio",
    "data_inicial",
    "issue_date_start",
    "modified_from",
    "from",
)
END_KEYS = (
    "date_end",
    "end_date",
    "date_to",
    "dataFim",
    "data_final",
    "issue_date_end",
    "modified_to",
    "to",
)

# Chaves internas — não devem ir na query HTTP da api-delpi.
INTERNAL_PARAM_KEYS = frozenset({DATE_RANGE_PRESET_KEY})


def find_date_range_keys(keys: Mapping[str, Any] | list[str] | tuple[str, ...] | None) -> tuple[str, str] | None:
    if keys is None:
        return None
    key_set = set(keys.keys() if isinstance(keys, Mapping) else keys)
    start = next((key for key in START_KEYS if key in key_set), None)
    end = next((key for key in END_KEYS if key in key_set), None)
    if start and end:
        return start, end
    return None


def compute_preset_range(
    preset: str,
    *,
    period_days: int | None = None,
    today: date | None = None,
) -> tuple[date, date] | None:
    """Retorna (início, fim) inclusivos. None = usar datas manuais (custom)."""
    day = today or date.today()
    normalized = (preset or "").strip().lower().replace("-", "_")
    if not normalized or normalized == "custom":
        return None

    if normalized == "today":
        return day, day

    if normalized == "this_week":
        start = day - timedelta(days=day.weekday())  # segunda
        return start, day

    if normalized == "this_month":
        return day.replace(day=1), day

    if normalized == "last_7_days":
        return day - timedelta(days=6), day

    if normalized == "last_30_days":
        return day - timedelta(days=29), day

    if normalized in {"last_n_days", "last_n", "period_days"}:
        n = max(int(period_days or 7), 1)
        return day - timedelta(days=n - 1), day

    return None


def _as_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    return text or None


def apply_date_range_preset(
    params: Mapping[str, Any] | None,
    *,
    schema_keys: Mapping[str, Any] | list[str] | tuple[str, ...] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Expande `dateRangePreset` / `periodDays` em datas concretas nos nomes do schema.

    Remove `dateRangePreset` do resultado (só uso interno do bloco TV).
    """
    merged: dict[str, Any] = {}
    if isinstance(params, Mapping):
        for key, value in params.items():
            if value is None or value == "":
                continue
            merged[str(key)] = value

    preset = str(merged.get(DATE_RANGE_PRESET_KEY) or "").strip()
    period_raw = merged.get(PERIOD_DAYS_KEY)
    try:
        period_days = int(period_raw) if period_raw is not None and period_raw != "" else None
    except (TypeError, ValueError):
        period_days = None

    pair = find_date_range_keys(schema_keys) or find_date_range_keys(merged)
    # Estratégia date_range do catálogo: canônico start_date/end_date.
    if pair is None and (preset or period_days is not None):
        pair = ("start_date", "end_date")

    if pair:
        start_key, end_key = pair
        computed = compute_preset_range(preset, period_days=period_days, today=today)
        if computed is not None:
            start_d, end_d = computed
            merged[start_key] = start_d.isoformat()
            merged[end_key] = end_d.isoformat()
            # Espelha aliases comuns usados pela api-delpi.
            if start_key != "start_date":
                merged.setdefault("start_date", start_d.isoformat())
            if end_key != "end_date":
                merged.setdefault("end_date", end_d.isoformat())
        elif period_days is not None and not _as_iso(merged.get(start_key)):
            start_d, end_d = date.today() - timedelta(days=max(period_days, 1) - 1), date.today()
            if today is not None:
                start_d, end_d = today - timedelta(days=max(period_days, 1) - 1), today
            merged[start_key] = start_d.isoformat()
            merged[end_key] = end_d.isoformat()

    merged.pop(DATE_RANGE_PRESET_KEY, None)
    return merged
