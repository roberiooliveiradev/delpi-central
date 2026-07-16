"""Presets relativos de período para fontes TV (datas sempre recalculadas no fetch)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping, Sequence

DATE_RANGE_PRESET_KEY = "dateRangePreset"
PERIOD_DAYS_KEY = "periodDays"

# Pares canônicos OpenAPI (ordem = preferência ao detectar no schema).
DATE_RANGE_KEY_PAIRS: tuple[tuple[str, str], ...] = (
    ("date_start", "date_end"),
    ("start_date", "end_date"),
    ("date_from", "date_to"),
    ("dataInicio", "dataFim"),
    ("data_inicial", "data_final"),
    ("issue_date_start", "issue_date_end"),
    ("modified_from", "modified_to"),
    ("from", "to"),
)

START_KEYS = tuple(pair[0] for pair in DATE_RANGE_KEY_PAIRS)
END_KEYS = tuple(pair[1] for pair in DATE_RANGE_KEY_PAIRS)

# Chaves internas — não devem ir na query HTTP da api-delpi.
INTERNAL_PARAM_KEYS = frozenset({DATE_RANGE_PRESET_KEY})

DEFAULT_DATE_RANGE_KEYS = ("start_date", "end_date")


def find_date_range_keys(keys: Mapping[str, Any] | list[str] | tuple[str, ...] | None) -> tuple[str, str] | None:
    if keys is None:
        return None
    key_set = set(keys.keys() if isinstance(keys, Mapping) else keys)
    for start, end in DATE_RANGE_KEY_PAIRS:
        if start in key_set and end in key_set:
            return start, end
    return None


def normalize_date_range_keys(raw: Any) -> tuple[str, str] | None:
    """Aceita lista/tupla `[start, end]` ou dict `{start, end}` do catálogo."""
    if isinstance(raw, Mapping):
        start = raw.get("start") or raw.get("startKey") or raw.get("start_key")
        end = raw.get("end") or raw.get("endKey") or raw.get("end_key")
        if start and end:
            return str(start), str(end)
        return None
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) >= 2:
        return str(raw[0]), str(raw[1])
    return None


def resolve_output_date_range_keys(
    *,
    schema_keys: Mapping[str, Any] | list[str] | tuple[str, ...] | None = None,
    date_range_keys: Any = None,
    strategy: str | None = None,
    fallback: tuple[str, str] = DEFAULT_DATE_RANGE_KEYS,
) -> tuple[str, str] | None:
    """Nomes HTTP canônicos da rota — nunca inferir a partir dos valores do usuário."""
    pair = find_date_range_keys(schema_keys) or normalize_date_range_keys(date_range_keys)
    if pair:
        return pair
    if str(strategy or "").strip().lower() == "date_range":
        return fallback
    return None


def read_date_range_values(
    params: Mapping[str, Any],
    start_key: str,
    end_key: str,
) -> tuple[Any, Any]:
    """Lê início/fim aceitando aliases (UI/legado), mas o caller emite só start_key/end_key."""
    start = params.get(start_key)
    end = params.get(end_key)
    if not _as_iso(start):
        for key in START_KEYS:
            if key == start_key:
                continue
            candidate = params.get(key)
            if _as_iso(candidate):
                start = candidate
                break
    if not _as_iso(end):
        for key in END_KEYS:
            if key == end_key:
                continue
            candidate = params.get(key)
            if _as_iso(candidate):
                end = candidate
                break
    return start, end


def date_alias_keys(*, keep: tuple[str, str]) -> frozenset[str]:
    keep_set = {keep[0], keep[1]}
    return frozenset(set(START_KEYS) | set(END_KEYS) | keep_set)


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

    if normalized == "this_quarter":
        quarter_start_month = ((day.month - 1) // 3) * 3 + 1
        return day.replace(month=quarter_start_month, day=1), day

    if normalized == "this_year":
        return day.replace(month=1, day=1), day

    if normalized == "previous_week":
        current_week_start = day - timedelta(days=day.weekday())
        return current_week_start - timedelta(days=7), current_week_start - timedelta(days=1)

    if normalized == "previous_month":
        current_month_start = day.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        return previous_month_end.replace(day=1), previous_month_end

    if normalized == "previous_quarter":
        current_quarter_month = ((day.month - 1) // 3) * 3 + 1
        current_quarter_start = day.replace(month=current_quarter_month, day=1)
        previous_quarter_end = current_quarter_start - timedelta(days=1)
        previous_quarter_month = ((previous_quarter_end.month - 1) // 3) * 3 + 1
        return previous_quarter_end.replace(month=previous_quarter_month, day=1), previous_quarter_end

    if normalized == "previous_year":
        previous_year = day.year - 1
        return date(previous_year, 1, 1), date(previous_year, 12, 31)

    if normalized == "last_7_days":
        return day - timedelta(days=6), day

    if normalized == "last_30_days":
        return day - timedelta(days=29), day

    if normalized == "last_90_days":
        return day - timedelta(days=89), day

    if normalized in {"last_n_days", "last_n", "period_days"}:
        n = max(int(period_days or 7), 1)
        return day - timedelta(days=n - 1), day

    return None


GRANULARITY_ORDER = ("day", "week", "month", "year")


def _bucket_count(start: date, end: date, granularity: str) -> int:
    if granularity == "day":
        return (end - start).days + 1
    if granularity == "week":
        week_start = start - timedelta(days=start.weekday())
        return ((end - week_start).days // 7) + 1
    if granularity == "month":
        return (end.year - start.year) * 12 + (end.month - start.month) + 1
    return end.year - start.year + 1


def resolve_adaptive_granularity(
    start: date,
    end: date,
    *,
    preferred: str = "day",
    max_buckets: int = 60,
) -> str:
    """Menor granularidade (a partir da preferida) cujo período cabe em max_buckets.

    Evita truncamento silencioso de séries longas (ex.: «este ano» com bucket diário).
    """
    if start > end:
        return preferred if preferred in GRANULARITY_ORDER else "day"
    normalized = str(preferred or "").strip().lower()
    start_index = GRANULARITY_ORDER.index(normalized) if normalized in GRANULARITY_ORDER else 0
    for granularity in GRANULARITY_ORDER[start_index:]:
        if _bucket_count(start, end, granularity) <= max(max_buckets, 1):
            return granularity
    return GRANULARITY_ORDER[-1]


def _as_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    return text or None


def apply_date_range_preset(
    params: Mapping[str, Any] | None,
    *,
    schema_keys: Mapping[str, Any] | list[str] | tuple[str, ...] | None = None,
    date_range_keys: Any = None,
    strategy: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Expande `dateRangePreset` / `periodDays` em datas concretas nos nomes canônicos.

    Remove `dateRangePreset` do resultado (só uso interno do bloco TV).
    Não espelha aliases (`start_date` + `date_start`) — evita query HTTP ambígua.
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

    pair = resolve_output_date_range_keys(
        schema_keys=schema_keys,
        date_range_keys=date_range_keys,
        strategy=strategy if (preset or period_days is not None) else None,
    )
    # Fallback legado: periodDays sem schema/estratégia → start_date/end_date.
    if pair is None and (preset or period_days is not None):
        pair = find_date_range_keys(merged) or DEFAULT_DATE_RANGE_KEYS

    if pair:
        start_key, end_key = pair
        computed = compute_preset_range(preset, period_days=period_days, today=today)
        if computed is not None:
            start_d, end_d = computed
            merged[start_key] = start_d.isoformat()
            merged[end_key] = end_d.isoformat()
        elif period_days is not None and not _as_iso(merged.get(start_key)):
            day = today or date.today()
            start_d, end_d = day - timedelta(days=max(period_days, 1) - 1), day
            # Se o valor canônico ainda não existe, tenta aliases antes de calcular.
            alias_start, alias_end = read_date_range_values(merged, start_key, end_key)
            if _as_iso(alias_start) and _as_iso(alias_end):
                merged[start_key] = str(alias_start).strip()
                merged[end_key] = str(alias_end).strip()
            else:
                merged[start_key] = start_d.isoformat()
                merged[end_key] = end_d.isoformat()
        else:
            alias_start, alias_end = read_date_range_values(merged, start_key, end_key)
            if _as_iso(alias_start):
                merged[start_key] = str(alias_start).strip()
            if _as_iso(alias_end):
                merged[end_key] = str(alias_end).strip()

    merged.pop(DATE_RANGE_PRESET_KEY, None)
    return merged
