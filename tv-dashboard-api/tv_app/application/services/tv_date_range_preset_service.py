"""Presets relativos de período para fontes TV (datas sempre recalculadas no fetch)."""

from __future__ import annotations

import calendar
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

DATE_RANGE_PRESET_KEY = "dateRangePreset"
PERIOD_DAYS_KEY = "periodDays"
EXCLUDE_WEEKENDS_KEY = "excludeWeekends"

# Calendário civil de negócio DELPI — alinhado a plugin-ui/periodPreset e docs TZ.
DEFAULT_BUSINESS_TIMEZONE = "America/Sao_Paulo"

# Pares canônicos OpenAPI (ordem = preferência ao detectar no schema).
# Canônico HTTP api-delpi primeiro; aliases legado depois (remoção planejada 2027-01).
DATE_RANGE_KEY_PAIRS: tuple[tuple[str, str], ...] = (
    ("start_date", "end_date"),
    ("date_start", "date_end"),
    ("date_from", "date_to"),
    ("dataInicio", "dataFim"),
    ("data_inicio", "data_fim"),
    ("data_inicial", "data_final"),
    ("issue_date_start", "issue_date_end"),
    ("modified_from", "modified_to"),
    ("from", "to"),
)

START_KEYS = tuple(pair[0] for pair in DATE_RANGE_KEY_PAIRS)
END_KEYS = tuple(pair[1] for pair in DATE_RANGE_KEY_PAIRS)

# Chaves internas — não devem ir na query HTTP da api-delpi.
INTERNAL_PARAM_KEYS = frozenset({DATE_RANGE_PRESET_KEY, EXCLUDE_WEEKENDS_KEY})

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


def business_timezone_name() -> str:
    """Fuso canônico para «hoje» dos presets (env TZ ou America/Sao_Paulo)."""
    raw = (os.getenv("TZ") or "").strip()
    return raw or DEFAULT_BUSINESS_TIMEZONE


def calendar_today(*, today: date | None = None, tz_name: str | None = None) -> date:
    """Dia civil atual no fuso de negócio — nunca depender só de date.today() do host."""
    if today is not None:
        return today
    name = (tz_name or business_timezone_name()).strip() or DEFAULT_BUSINESS_TIMEZONE
    try:
        return datetime.now(ZoneInfo(name)).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def previous_business_day(day: date) -> date:
    """Dia útil anterior (seg–sex). Segunda → sexta; domingo/sábado → sexta."""
    candidate = day - timedelta(days=1)
    while candidate.weekday() >= 5:  # 5=sábado, 6=domingo
        candidate -= timedelta(days=1)
    return candidate


def shift_years(day: date, years: int) -> date:
    """Mesmo mês/dia N anos antes/depois; 29/02 em ano não-bissexto → 28/02."""
    target_year = day.year + years
    last_day = calendar.monthrange(target_year, day.month)[1]
    return date(target_year, day.month, min(day.day, last_day))


def compute_preset_range(
    preset: str,
    *,
    period_days: int | None = None,
    today: date | None = None,
) -> tuple[date, date] | None:
    """Retorna (início, fim) inclusivos. None = usar datas manuais (custom)."""
    day = calendar_today(today=today)
    normalized = (preset or "").strip().lower().replace("-", "_")
    if not normalized or normalized == "custom":
        return None

    if normalized == "today":
        return day, day

    # Reuniões do «dia anterior»: pula fim de semana (segunda → sexta).
    if normalized in {"previous_day", "yesterday", "previous_business_day"}:
        prior = previous_business_day(day)
        return prior, prior

    if normalized == "this_week":
        start = day - timedelta(days=day.weekday())  # segunda
        return start, day

    # Semana civil completa (segunda → domingo), mesmo que o fim seja futuro.
    if normalized == "this_week_full":
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=6)

    if normalized == "this_month":
        return day.replace(day=1), day

    # Mês civil completo (1 → último dia), mesmo que o fim seja futuro.
    if normalized == "this_month_full":
        start = day.replace(day=1)
        last_day = calendar.monthrange(day.year, day.month)[1]
        return start, day.replace(day=last_day)

    # MTD sem o dia corrente — fim = dia útil anterior (segunda → sexta).
    if normalized in {
        "this_month_until_yesterday",
        "this_month_to_yesterday",
        "this_month_until_previous_day",
    }:
        start = day.replace(day=1)
        end = previous_business_day(day)
        if end < start:
            # 1º dia útil do mês (ou 1º após FDS): ainda não há dia concluído no mês.
            return start, start
        return start, end

    if normalized == "this_quarter":
        quarter_start_month = ((day.month - 1) // 3) * 3 + 1
        return day.replace(month=quarter_start_month, day=1), day

    # Trimestre civil completo (1º dia → último dia do 3º mês).
    if normalized == "this_quarter_full":
        quarter_start_month = ((day.month - 1) // 3) * 3 + 1
        start = day.replace(month=quarter_start_month, day=1)
        end_month = quarter_start_month + 2
        last_day = calendar.monthrange(day.year, end_month)[1]
        return start, day.replace(month=end_month, day=last_day)

    if normalized == "this_year":
        return day.replace(month=1, day=1), day

    # Ano civil completo (01-01 → 12-31).
    if normalized == "this_year_full":
        return date(day.year, 1, 1), date(day.year, 12, 31)

    if normalized == "previous_week":
        current_week_start = day - timedelta(days=day.weekday())
        return current_week_start - timedelta(days=7), current_week_start - timedelta(days=1)

    if normalized == "previous_month":
        current_month_start = day.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        return previous_month_end.replace(day=1), previous_month_end

    # Mês civil completo do mesmo número no ano anterior (≠ mês passado, ≠ SPLY YTD).
    # Ex.: hoje=25/09/2026 → 01/09/2025 … 30/09/2025.
    if normalized in {
        "this_month_previous_year",
        "this_month_last_year",
        "same_month_previous_year",
    }:
        target_year = day.year - 1
        last_day = calendar.monthrange(target_year, day.month)[1]
        return date(target_year, day.month, 1), date(target_year, day.month, last_day)

    if normalized == "previous_quarter":
        current_quarter_month = ((day.month - 1) // 3) * 3 + 1
        current_quarter_start = day.replace(month=current_quarter_month, day=1)
        previous_quarter_end = current_quarter_start - timedelta(days=1)
        previous_quarter_month = ((previous_quarter_end.month - 1) // 3) * 3 + 1
        return previous_quarter_end.replace(month=previous_quarter_month, day=1), previous_quarter_end

    if normalized == "previous_year":
        previous_year = day.year - 1
        return date(previous_year, 1, 1), date(previous_year, 12, 31)

    # Espelho de «Este ano (até hoje)» no ano civil anterior (YoY / SPLY).
    # Ex.: hoje=24/09/2026 → 01/01/2025 … 24/09/2025. Distinto de previous_year (01/01–31/12).
    if normalized in {
        "same_period_previous_year",
        "previous_year_same_range",
        "previous_year_ytd",
        "same_period_last_year",
    }:
        end = shift_years(day, -1)
        return date(end.year, 1, 1), end

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


# Anos fora desta faixa (ex.: 0026 digitado no input type=date) estouram o
# limite de 24 meses da api-delpi quando o gateway completa a ponta faltante.
_MIN_SANE_YEAR = 1990
_MAX_SANE_YEAR = 2100


def _as_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = date.fromisoformat(text[:10])
    except ValueError:
        return None
    if parsed.year < _MIN_SANE_YEAR or parsed.year > _MAX_SANE_YEAR:
        return None
    return parsed.isoformat()


def drop_insane_date_values(params: dict[str, Any]) -> dict[str, Any]:
    """Remove datas com ano absurdo (ex.: 0026) de start/end e aliases."""
    out = dict(params)
    for key in (*START_KEYS, *END_KEYS):
        if key not in out:
            continue
        if _as_iso(out.get(key)) is None:
            out.pop(key, None)
    return out


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
    merged = drop_insane_date_values(merged)

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
        alias_start, alias_end = read_date_range_values(merged, start_key, end_key)
        explicit_start = _as_iso(merged.get(start_key)) or _as_iso(alias_start)
        explicit_end = _as_iso(merged.get(end_key)) or _as_iso(alias_end)
        # Preset relativo sempre recalcula (datas absolutas na mesma carga são stale —
        # a UI as esconde quando Período ≠ Personalizado). custom / ausente → manuais.
        computed = compute_preset_range(preset, period_days=period_days, today=today)
        if computed is not None:
            start_d, end_d = computed
            merged[start_key] = start_d.isoformat()
            merged[end_key] = end_d.isoformat()
        elif period_days is not None and not _as_iso(merged.get(start_key)):
            day = calendar_today(today=today)
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
            if explicit_start:
                merged[start_key] = str(explicit_start).strip()
            if explicit_end:
                merged[end_key] = str(explicit_end).strip()

    merged.pop(DATE_RANGE_PRESET_KEY, None)
    return merged
