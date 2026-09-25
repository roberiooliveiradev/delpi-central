"""Display formatting ownership for TV slides — Python port of plugin-ui formatDisplayValue.

Corpus must stay mirrored with `plugins/plugin-ui/src/displayFormat/formatDisplayValue.test.ts`.
See ADR `tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md`.
"""

from __future__ import annotations

import math
import re
from typing import Any

from tv_app.application.services.data.display_format_hints_service import (
    DisplayFormatHintsService,
)

EMPTY_DISPLAY = "—"

_MONTH_ABBREV_PT = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)
_MONTH_FULL_PT = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
_WEEKDAY_FULL_PT = (
    "domingo",
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
)

_MONTH_ABBREV_PARSE: dict[str, int] = {
    "jan": 0,
    "fev": 1,
    "feb": 1,
    "mar": 2,
    "abr": 3,
    "apr": 3,
    "mai": 4,
    "may": 4,
    "jun": 5,
    "jul": 6,
    "ago": 7,
    "aug": 7,
    "set": 8,
    "sep": 8,
    "sept": 8,
    "out": 9,
    "oct": 9,
    "nov": 10,
    "dez": 11,
    "dec": 11,
}

_EN_MONTH_TO_PT_LABEL: dict[str, str] = {
    "jan": "Jan",
    "feb": "Fev",
    "mar": "Mar",
    "apr": "Abr",
    "may": "Mai",
    "jun": "Jun",
    "jul": "Jul",
    "aug": "Ago",
    "sep": "Set",
    "sept": "Set",
    "oct": "Out",
    "nov": "Nov",
    "dec": "Dez",
}

_DATE_HINT = re.compile(r"dd|yyyy|aaaa|mmmm|mmm|mm|HH|hh|ss|yy", re.IGNORECASE)
_LOCALIZED_MONTH_YEAR = re.compile(
    r"^(jan|fev|feb|mar|abr|apr|mai|may|jun|jul|ago|aug|set|sep|sept|out|oct|nov|dez|dec)"
    r"\.?\s+de\s+(\d{2}|\d{4})$",
    re.IGNORECASE,
)
_EN_MONTH_TOKEN = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b(\.)?",
    re.IGNORECASE,
)

_PRESETS: dict[str, dict[str, Any]] = {
    "general": {"category": "general"},
    "number-0": {
        "category": "number",
        "decimalPlaces": 0,
        "useThousandsSeparator": True,
    },
    "number-2": {
        "category": "number",
        "decimalPlaces": 2,
        "useThousandsSeparator": False,
    },
    "number-thousands": {
        "category": "number",
        "decimalPlaces": 2,
        "useThousandsSeparator": True,
    },
    "number-compact": {
        "category": "number",
        "presetId": "number-compact",
        "decimalPlaces": 1,
    },
    "currency-brl": {
        "category": "currency",
        "currency": "BRL",
        "decimalPlaces": 2,
    },
    "currency-brl-4": {
        "category": "currency",
        "currency": "BRL",
        "decimalPlaces": 4,
    },
    "accounting": {
        "category": "accounting",
        "currency": "BRL",
        "decimalPlaces": 2,
    },
    "date-short": {
        "category": "date",
        "presetId": "date-short",
        "pattern": "dd/mm/yyyy",
    },
    "date-short-yy": {
        "category": "date",
        "presetId": "date-short-yy",
        "pattern": "dd/mm/yy",
    },
    "date-long": {"category": "date", "presetId": "date-long"},
    "date-iso": {
        "category": "date",
        "presetId": "date-iso",
        "pattern": "yyyy-mm-dd",
    },
    "date-day-mon": {"category": "date", "presetId": "date-day-mon"},
    "date-month": {"category": "date", "presetId": "date-month"},
    "date-year": {"category": "date", "presetId": "date-year"},
    "date-year-yy": {
        "category": "date",
        "presetId": "date-year-yy",
        "pattern": "yy",
    },
    "date-auto": {"category": "date", "presetId": "date-auto"},
    "date-month-year": {
        "category": "date",
        "presetId": "date-month-year",
        "pattern": "mm/yyyy",
    },
    "date-month-year-yy": {
        "category": "date",
        "presetId": "date-month-year-yy",
        "pattern": "mm/yy",
    },
    "date-month-year-dash": {
        "category": "date",
        "presetId": "date-month-year-dash",
        "pattern": "mm-yyyy",
    },
    "date-month-year-dash-yy": {
        "category": "date",
        "presetId": "date-month-year-dash-yy",
        "pattern": "mm-yy",
    },
    "date-year-month": {
        "category": "date",
        "presetId": "date-year-month",
        "pattern": "yyyy/mm",
    },
    "date-year-month-yy": {
        "category": "date",
        "presetId": "date-year-month-yy",
        "pattern": "yy/mm",
    },
    "date-month-abbrev-year": {
        "category": "date",
        "presetId": "date-month-abbrev-year",
        "pattern": 'mmm"."/yyyy',
    },
    "date-month-abbrev-year-yy": {
        "category": "date",
        "presetId": "date-month-abbrev-year-yy",
        "pattern": 'mmm"."/yy',
    },
    "date-month-full-year": {
        "category": "date",
        "presetId": "date-month-full-year",
        "pattern": "mmmm/yyyy",
    },
    "date-month-full-year-yy": {
        "category": "date",
        "presetId": "date-month-full-year-yy",
        "pattern": "mmmm/yy",
    },
    "date-month-abbrev-de-year": {
        "category": "date",
        "presetId": "date-month-abbrev-de-year",
        "pattern": 'mmm "de" yyyy',
    },
    "date-month-full-de-year": {
        "category": "date",
        "presetId": "date-month-full-de-year",
        "pattern": 'mmmm "de" yyyy',
    },
    "date-day-mon-year": {
        "category": "date",
        "presetId": "date-day-mon-year",
        "pattern": 'dd mmm"." yyyy',
    },
    "date-day-mon-year-yy": {
        "category": "date",
        "presetId": "date-day-mon-year-yy",
        "pattern": 'dd mmm"." yy',
    },
    "date-day-full-long": {
        "category": "date",
        "presetId": "date-day-full-long",
        "pattern": 'dd "de" mmmm "de" yyyy',
    },
    "date-day-full-long-yy": {
        "category": "date",
        "presetId": "date-day-full-long-yy",
        "pattern": 'dd "de" mmmm "de" yy',
    },
    "date-month-num": {
        "category": "date",
        "presetId": "date-month-num",
        "pattern": "mm",
    },
    "date-month-abbrev": {
        "category": "date",
        "presetId": "date-month-abbrev",
        "pattern": 'mmm"."',
    },
    "date-month-full": {
        "category": "date",
        "presetId": "date-month-full",
        "pattern": "mmmm",
    },
    "time-hhmm": {"category": "time", "pattern": "HH:mm"},
    "percent": {"category": "percent", "decimalPlaces": 1},
    "scientific": {"category": "scientific", "decimalPlaces": 2},
    "text": {"category": "text"},
    "custom": {"category": "custom", "pattern": ""},
}

# UI catalog metadata (labels/patterns for picker). Spec authority remains `_PRESETS`.
_FORMAT_CATALOG: tuple[dict[str, Any], ...] = (
    {"formatId": "general", "category": "general", "label": "Geral", "pattern": None, "compatibleTypes": ("any",)},
    {"formatId": "number-0", "category": "number", "label": "0 casas", "pattern": "0", "compatibleTypes": ("number", "any")},
    {"formatId": "number-2", "category": "number", "label": "2 casas", "pattern": "0,00", "compatibleTypes": ("number", "any")},
    {
        "formatId": "number-thousands",
        "category": "number",
        "label": "Milhar",
        "pattern": "#.##0,00",
        "compatibleTypes": ("number", "any"),
    },
    {
        "formatId": "number-compact",
        "category": "number",
        "label": "Compacto",
        "pattern": None,
        "compatibleTypes": ("number", "any"),
    },
    {
        "formatId": "currency-brl",
        "category": "currency",
        "label": "Real (BRL)",
        "pattern": "R$ #.##0,00",
        "compatibleTypes": ("number", "currency", "any"),
    },
    {
        "formatId": "currency-brl-4",
        "category": "currency",
        "label": "Real (4 casas)",
        "pattern": "R$ #.##0,0000",
        "compatibleTypes": ("number", "currency", "any"),
    },
    {
        "formatId": "accounting",
        "category": "accounting",
        "label": "Contábil (R$)",
        "pattern": "R$ #.##0,00",
        "compatibleTypes": ("number", "currency", "any"),
    },
    {
        "formatId": "date-short",
        "category": "date",
        "label": "Data curta",
        "pattern": "dd/MM/yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-short-yy",
        "category": "date",
        "label": "Data curta (ano curto)",
        "pattern": "dd/MM/yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-year",
        "category": "date",
        "label": "Mês/ano",
        "pattern": "MM/yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-year-yy",
        "category": "date",
        "label": "Mês/ano curto",
        "pattern": "MM/yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-year-dash",
        "category": "date",
        "label": "Mês-ano",
        "pattern": "MM-yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-year-dash-yy",
        "category": "date",
        "label": "Mês-ano curto",
        "pattern": "MM-yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-year-month",
        "category": "date",
        "label": "Ano/mês",
        "pattern": "yyyy/MM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-year-month-yy",
        "category": "date",
        "label": "Ano curto/mês",
        "pattern": "yy/MM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-abbrev-year",
        "category": "date",
        "label": "Mês abreviado/ano",
        "pattern": "MMM/yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-abbrev-year-yy",
        "category": "date",
        "label": "Mês abreviado/ano curto",
        "pattern": "MMM/yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-full-year",
        "category": "date",
        "label": "Mês por extenso/ano",
        "pattern": "MMMM/yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-full-year-yy",
        "category": "date",
        "label": "Mês por extenso/ano curto",
        "pattern": "MMMM/yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-abbrev-de-year",
        "category": "date",
        "label": "Mês abreviado de ano",
        "pattern": "MMM 'de' yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-full-de-year",
        "category": "date",
        "label": "Mês de ano",
        "pattern": "MMMM 'de' yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-day-mon-year",
        "category": "date",
        "label": "Dia mês ano",
        "pattern": "dd MMM yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-day-mon-year-yy",
        "category": "date",
        "label": "Dia mês ano curto",
        "pattern": "dd MMM yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-day-full-long",
        "category": "date",
        "label": "Dia de mês de ano",
        "pattern": "dd 'de' MMMM 'de' yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-day-full-long-yy",
        "category": "date",
        "label": "Dia de mês de ano curto",
        "pattern": "dd 'de' MMMM 'de' yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-iso",
        "category": "date",
        "label": "ISO",
        "pattern": "yyyy-MM-dd",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-day-mon",
        "category": "date",
        "label": "Dia mês",
        "pattern": "dd MMM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month",
        "category": "date",
        "label": "Mês de ano (legado)",
        "pattern": "MMM. 'de' yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-year",
        "category": "date",
        "label": "Ano",
        "pattern": "yyyy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-year-yy",
        "category": "date",
        "label": "Ano curto",
        "pattern": "yy",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-num",
        "category": "date",
        "label": "Mês (número)",
        "pattern": "MM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-abbrev",
        "category": "date",
        "label": "Mês abreviado",
        "pattern": "MMM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-month-full",
        "category": "date",
        "label": "Mês por extenso",
        "pattern": "MMMM",
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-long",
        "category": "date",
        "label": "Data completa",
        "pattern": None,
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "date-auto",
        "category": "date",
        "label": "Data (auto)",
        "pattern": None,
        "compatibleTypes": ("date", "datetime", "any"),
    },
    {
        "formatId": "time-hhmm",
        "category": "time",
        "label": "Hora",
        "pattern": "HH:mm",
        "compatibleTypes": ("time", "datetime", "any"),
    },
    {
        "formatId": "percent",
        "category": "percent",
        "label": "Porcentagem",
        "pattern": "0,0%",
        "compatibleTypes": ("number", "percent", "any"),
    },
    {
        "formatId": "scientific",
        "category": "scientific",
        "label": "Científico",
        "pattern": "0,00E+00",
        "compatibleTypes": ("number", "any"),
    },
    {"formatId": "text", "category": "text", "label": "Texto", "pattern": None, "compatibleTypes": ("any", "text")},
)

_REASON_MESSAGES_PT: dict[str, str] = {
    "TYPE_INCOMPATIBLE": "Este formato não é compatível com o tipo do valor.",
    "VALUE_NULL": "Não há valor para formatar.",
    "VALUE_MISSING": "Valor ausente.",
    "VALUE_EMPTY": "O valor está vazio.",
    "VALUE_INVALID": "O valor atual não pode ser convertido para este formato.",
    "PARSE_FAILED": "Não foi possível interpretar o valor.",
    "FORMAT_UNSUPPORTED": "Formato não suportado.",
    "VALUE_NOT_DATE": "O valor atual não pode ser convertido para data.",
    "VALUE_NOT_NUMBER": "O valor atual não pode ser convertido para número.",
    "VALUE_NOT_TIME": "O valor atual não pode ser convertido para hora.",
}

_FIELD_LIST_JOIN = "\n"
_TIME_SERIES_COLUMN_KEYS = frozenset(
    {
        "periodo",
        "period",
        "date",
        "data",
        "competence",
        "competencia",
        "mes",
        "month",
        "bucket",
        "day",
        "dia",
    }
)
_IDD_ALIASES = {"score": ("idd",), "idd": ("score",)}


def month_abbrev_pt(month_index0: int, *, capitalize: bool = True) -> str:
    abbrev = _MONTH_ABBREV_PT[((month_index0 % 12) + 12) % 12]
    if capitalize:
        return f"{abbrev[0].upper()}{abbrev[1:]}"
    return abbrev


def month_full_pt(month_index0: int) -> str:
    return _MONTH_FULL_PT[((month_index0 % 12) + 12) % 12]


def weekday_full_pt(year: int, month: int, day: int) -> str:
    # Calendar weekday via pure Python (UTC date-only).
    from datetime import date

    try:
        weekday = date(year, month + 1, day).weekday()  # Mon=0
    except ValueError:
        return ""
    # Convert Mon=0 → Sun=0 index used by WEEKDAY_FULL_PT
    sun_index = (weekday + 1) % 7
    return _WEEKDAY_FULL_PT[sun_index]


def parse_display_date(raw: Any) -> dict[str, Any] | None:
    """ISO date-only = UTC calendar parts (no local TZ shift)."""
    if isinstance(raw, (int, float)) and math.isfinite(raw):
        return _from_unix_ms(float(raw))
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None

    ym = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if ym:
        year, month = int(ym.group(1)), int(ym.group(2))
        if month < 1 or month > 12:
            return None
        return {
            "year": year,
            "month": month - 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "dateOnly": True,
        }

    ymd = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if ymd:
        year, month, day = int(ymd.group(1)), int(ymd.group(2)), int(ymd.group(3))
        if month < 1 or month > 12 or day < 1 or day > 31:
            return None
        return {
            "year": year,
            "month": month - 1,
            "day": day,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "dateOnly": True,
        }

    ymd_time = re.fullmatch(
        r"(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?",
        text,
    )
    if ymd_time:
        has_zone = bool(ymd_time.group(7))
        if has_zone:
            from datetime import datetime

            try:
                normalized = text.replace("Z", "+00:00")
                if re.search(r"[+-]\d{4}$", normalized):
                    normalized = normalized[:-2] + ":" + normalized[-2:]
                dt = datetime.fromisoformat(normalized)
            except ValueError:
                return None
            return {
                "year": dt.year,
                "month": dt.month - 1,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
                "dateOnly": False,
            }
        return {
            "year": int(ymd_time.group(1)),
            "month": int(ymd_time.group(2)) - 1,
            "day": int(ymd_time.group(3)),
            "hour": int(ymd_time.group(4)),
            "minute": int(ymd_time.group(5)),
            "second": int(ymd_time.group(6) or 0),
            "dateOnly": False,
        }

    br = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if br:
        day, month, year = int(br.group(1)), int(br.group(2)), int(br.group(3))
        if month < 1 or month > 12 or day < 1 or day > 31:
            return None
        return {
            "year": year,
            "month": month - 1,
            "day": day,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "dateOnly": True,
        }

    month_de = _parse_localized_month_year_label(text)
    if month_de:
        return month_de
    return None


def is_localized_chart_period_label(raw: str) -> bool:
    return _parse_localized_month_year_label(raw.strip()) is not None


def localize_english_month_tokens_in_label(raw: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        key = match.group(1).lower()
        pt = _EN_MONTH_TO_PT_LABEL.get(key, match.group(1))
        return f"{pt}{match.group(2) or ''}"

    return _EN_MONTH_TOKEN.sub(_repl, raw)


def _parse_localized_month_year_label(text: str) -> dict[str, Any] | None:
    match = _LOCALIZED_MONTH_YEAR.fullmatch(text)
    if not match:
        return None
    month = _MONTH_ABBREV_PARSE.get(match.group(1).lower())
    if month is None:
        return None
    year = int(match.group(2))
    if year < 100:
        year += 2000
    return {
        "year": year,
        "month": month,
        "day": 1,
        "hour": 0,
        "minute": 0,
        "second": 0,
        "dateOnly": True,
    }


def _from_unix_ms(ms: float) -> dict[str, Any]:
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(ms / 1000.0 if ms > 1e12 else ms, tz=timezone.utc)
    return {
        "year": dt.year,
        "month": dt.month - 1,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "dateOnly": False,
    }


def _pad2(n: int) -> str:
    return str(n).zfill(2)


def _clamp_places(raw: Any, fallback: int) -> int:
    try:
        if isinstance(raw, (int, float)) and math.isfinite(float(raw)):
            return min(8, max(0, int(raw)))
    except (TypeError, ValueError):
        pass
    return fallback


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    if isinstance(value, str) and value.strip():
        cleaned = value.strip().replace(" ", "").replace(",", ".")
        try:
            n = float(cleaned)
        except ValueError:
            return None
        return n if math.isfinite(n) else None
    return None


def _is_zero_padded_numeric_code(value: Any) -> bool:
    """Digit string with leading zeros (filial 01, codes) — not a real number for Geral."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    if len(text) < 2 or not text.isdigit():
        return False
    return text.startswith("0")


def _stringify_fallback(value: Any) -> str:
    if value is None or value == "":
        return EMPTY_DISPLAY
    return str(value)


def _round_half_up(value: float, places: int) -> float:
    """Match Intl/JS half-up (Python round() is bankers)."""
    from decimal import Decimal, ROUND_HALF_UP

    quant = Decimal("1").scaleb(-places) if places > 0 else Decimal("1")
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))


def _format_pt_br_number(
    value: float,
    *,
    min_fraction: int,
    max_fraction: int,
    use_grouping: bool = True,
) -> str:
    if max_fraction < 0:
        max_fraction = 0
    if min_fraction < 0:
        min_fraction = 0
    if min_fraction > max_fraction:
        min_fraction = max_fraction
    rounded = _round_half_up(value, max_fraction)
    sign = "-" if rounded < 0 else ""
    abs_val = abs(rounded)
    if max_fraction == 0:
        int_part = str(int(abs_val))
        frac = ""
    else:
        fixed = f"{abs_val:.{max_fraction}f}"
        int_str, frac_str = fixed.split(".")
        if min_fraction < max_fraction:
            frac_str = frac_str.rstrip("0")
            if len(frac_str) < min_fraction:
                frac_str = frac_str.ljust(min_fraction, "0")
        else:
            frac_str = frac_str[:max_fraction].ljust(min_fraction, "0")
        int_part = int_str
        frac = frac_str
    if use_grouping:
        digits = list(int_part)
        grouped: list[str] = []
        while digits:
            chunk = "".join(digits[-3:])
            grouped.insert(0, chunk)
            digits = digits[:-3]
        int_part = ".".join(grouped) if grouped else "0"
    if frac:
        return f"{sign}{int_part},{frac}"
    return f"{sign}{int_part}"


def _format_compact_pt_br(value: float, decimal_places: int) -> str:
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val < 1000:
        return _format_pt_br_number(
            value, min_fraction=0, max_fraction=decimal_places, use_grouping=True
        )
    if abs_val < 1_000_000:
        scaled = abs_val / 1000.0
        body = _format_pt_br_number(
            scaled, min_fraction=0, max_fraction=decimal_places, use_grouping=False
        )
        return f"{sign}{body} mil"
    if abs_val < 1_000_000_000:
        scaled = abs_val / 1_000_000.0
        body = _format_pt_br_number(
            scaled, min_fraction=0, max_fraction=decimal_places, use_grouping=False
        )
        return f"{sign}{body} mi"
    scaled = abs_val / 1_000_000_000.0
    body = _format_pt_br_number(
        scaled, min_fraction=0, max_fraction=decimal_places, use_grouping=False
    )
    return f"{sign}{body} bi"


def _pattern_looks_like_date(pattern: str) -> bool:
    stripped = re.sub(r'"[^"]*"', "", pattern)
    return bool(_DATE_HINT.search(stripped))


def format_custom_pattern(value: Any, pattern: str) -> str | None:
    trimmed = pattern.strip()
    if not trimmed:
        return None
    if _pattern_looks_like_date(trimmed):
        date = parse_display_date(value)
        if not date:
            return None
        return _format_date_pattern(date, trimmed)
    num = _coerce_number(value)
    if num is None:
        return None
    return _format_number_pattern(num, trimmed)


def _format_date_pattern(date: dict[str, Any], pattern: str) -> str:
    out: list[str] = []
    i = 0
    seen_hour = False
    while i < len(pattern):
        if pattern[i] == '"':
            end = pattern.find('"', i + 1)
            if end < 0:
                out.append(pattern[i:])
                break
            out.append(pattern[i + 1 : end])
            i = end + 1
            continue
        rest = pattern[i:]
        if rest.startswith("mmmm"):
            out.append(month_full_pt(int(date["month"])))
            i += 4
            continue
        if rest.startswith("mmm"):
            out.append(month_abbrev_pt(int(date["month"]), capitalize=False))
            i += 3
            continue
        if rest.startswith("aaaa") or rest.startswith("yyyy"):
            out.append(str(date["year"]))
            i += 4
            continue
        if rest.startswith("dddd"):
            out.append(
                weekday_full_pt(int(date["year"]), int(date["month"]), int(date["day"]))
            )
            i += 4
            continue
        if rest.startswith("HH") or rest.startswith("hh"):
            out.append(_pad2(int(date["hour"])))
            seen_hour = True
            i += 2
            continue
        if rest.startswith("ss"):
            out.append(_pad2(int(date["second"])))
            i += 2
            continue
        if rest.startswith("mm"):
            out.append(
                _pad2(int(date["minute"]) if seen_hour else int(date["month"]) + 1)
            )
            i += 2
            continue
        if rest.startswith("dd"):
            out.append(_pad2(int(date["day"])))
            i += 2
            continue
        if rest.startswith("yy"):
            out.append(str(date["year"])[-2:].zfill(2))
            i += 2
            continue
        out.append(pattern[i])
        i += 1
    return "".join(out)


def _format_number_pattern(value: float, pattern: str) -> str:
    parts: list[tuple[str, str]] = []
    i = 0
    while i < len(pattern):
        if pattern[i] == '"':
            end = pattern.find('"', i + 1)
            if end < 0:
                parts.append(("lit", pattern[i:]))
                break
            parts.append(("lit", pattern[i + 1 : end]))
            i = end + 1
            continue
        j = i
        while j < len(pattern) and pattern[j] != '"':
            j += 1
        chunk = pattern[i:j]
        if re.search(r"[0#E%,.]", chunk):
            parts.append(("mask", chunk))
        else:
            parts.append(("lit", chunk))
        i = j

    mask = "".join(p[1] for p in parts if p[0] == "mask")
    core = _format_numeric_mask_core(value, mask)
    used = False
    out: list[str] = []
    for kind, part in parts:
        if kind == "lit":
            out.append(part)
        elif not used:
            used = True
            out.append(core)
    return "".join(out)


def _format_numeric_mask_core(value: float, mask: str) -> str:
    is_percent = "%" in mask
    sci = bool(re.search(r"E\+0+", mask, re.IGNORECASE))
    cleaned = re.sub(r"%", "", mask)
    cleaned = re.sub(r"E\+0+", "", cleaned, flags=re.IGNORECASE).strip()
    decimal_places = 0
    comma = cleaned.rfind(",")
    if comma >= 0:
        decimal_places = len(re.sub(r"[^0#]", "", cleaned[comma + 1 :]))
    use_thousands = bool(
        re.search(r"\d.*\.\d{3}|#\.#|#\.##0", cleaned)
        or ".#" in cleaned
        or "#." in cleaned
    )
    abs_val = abs(value)
    if sci:
        exp = 0 if abs_val == 0 else math.floor(math.log10(abs_val))
        mantissa = 0.0 if abs_val == 0 else abs_val / (10**exp)
        places = decimal_places or 2
        man_str = _format_pt_br_number(
            mantissa, min_fraction=places, max_fraction=places, use_grouping=False
        )
        exp_str = f"{'+' if exp >= 0 else '-'}{abs(exp):02d}"
        return f"{'-' if value < 0 else ''}{man_str}E{exp_str}"
    formatted = _format_pt_br_number(
        abs_val,
        min_fraction=decimal_places,
        max_fraction=decimal_places,
        use_grouping=use_thousands,
    )
    return f"{'-' if value < 0 else ''}{formatted}{'%' if is_percent else ''}"


def _format_date_spec(date: dict[str, Any], spec: dict[str, Any], raw: str) -> str:
    preset = str(spec.get("presetId") or "")
    category = str(spec.get("category") or "")

    if category == "time" or preset == "time-hhmm":
        pattern = str(spec.get("pattern") or "").strip()
        if pattern:
            return format_custom_pattern(raw, pattern) or (
                f"{_pad2(int(date['hour']))}:{_pad2(int(date['minute']))}"
            )
        return f"{_pad2(int(date['hour']))}:{_pad2(int(date['minute']))}"

    pattern = str(spec.get("pattern") or "").strip()
    if pattern and preset not in {"date-long", "date-auto", "date-day-mon"}:
        # Date-category patterns always format via date tokens (mm = month even alone).
        return _format_date_pattern(date, pattern)

    if preset == "date-iso":
        return f"{date['year']}-{_pad2(int(date['month']) + 1)}-{_pad2(int(date['day']))}"
    if preset == "date-year":
        return str(date["year"])
    if preset == "date-month":
        return f"{month_abbrev_pt(int(date['month']))}. de {date['year']}"
    if preset == "date-day-mon":
        return (
            f"{_pad2(int(date['day']))} "
            f"{month_abbrev_pt(int(date['month']), capitalize=False)}"
        )
    if preset == "date-long":
        return (
            f"{weekday_full_pt(int(date['year']), int(date['month']), int(date['day']))}, "
            f"{date['day']} de {month_full_pt(int(date['month']))} de {date['year']}"
        )
    if preset == "date-auto":
        has_day = bool(re.match(r"^\d{4}-\d{2}-\d{2}", raw.strip()))
        if has_day:
            return (
                f"{_pad2(int(date['day']))} {month_abbrev_pt(int(date['month']))}"
            )
        return f"{month_abbrev_pt(int(date['month']))}/{str(date['year'])[-2:]}"

    # date-short default
    return f"{_pad2(int(date['day']))}/{_pad2(int(date['month']) + 1)}/{date['year']}"


def _format_number_spec(value: float, spec: dict[str, Any]) -> str:
    preset_id = str(spec.get("presetId") or "")
    category = str(spec.get("category") or "")

    if preset_id == "number-compact" or (
        category == "number" and preset_id == "number-compact"
    ):
        return _format_compact_pt_br(value, _clamp_places(spec.get("decimalPlaces"), 1))

    if category == "percent":
        digits = _clamp_places(spec.get("decimalPlaces"), 1)
        body = _format_pt_br_number(
            value, min_fraction=digits, max_fraction=digits, use_grouping=True
        )
        return f"{body}%"

    if category == "scientific":
        digits = _clamp_places(spec.get("decimalPlaces"), 2)
        exp = f"{value:.{digits}e}".replace(".", ",").replace("e", "E")
        return exp

    if category in {"currency", "accounting"}:
        digits = _clamp_places(
            spec.get("decimalPlaces"),
            4 if preset_id == "currency-brl-4" else 2,
        )
        body = _format_pt_br_number(
            value, min_fraction=digits, max_fraction=digits, use_grouping=True
        )
        # Intl pt-BR uses NBSP between symbol and amount.
        return f"R$\xa0{body}"

    if category == "number":
        has_explicit = isinstance(spec.get("decimalPlaces"), (int, float)) and math.isfinite(
            float(spec["decimalPlaces"])
        )
        if has_explicit:
            digits = _clamp_places(spec.get("decimalPlaces"), 2)
        elif preset_id == "number-0":
            digits = 0
        else:
            digits = 2
        thousands = (
            bool(spec["useThousandsSeparator"])
            if isinstance(spec.get("useThousandsSeparator"), bool)
            else preset_id != "number-2"
        )
        pad_exact = has_explicit or preset_id in {"number-2", "number-0"}
        return _format_pt_br_number(
            value,
            min_fraction=digits if pad_exact else 0,
            max_fraction=digits,
            use_grouping=thousands,
        )

    # general
    has_explicit = isinstance(spec.get("decimalPlaces"), (int, float)) and math.isfinite(
        float(spec["decimalPlaces"])
    )
    if has_explicit:
        digits = _clamp_places(spec.get("decimalPlaces"), 2)
        return _format_pt_br_number(
            value, min_fraction=digits, max_fraction=digits, use_grouping=True
        )
    return _format_pt_br_number(
        value, min_fraction=0, max_fraction=2, use_grouping=True
    )


class DisplayFormatService:
    """Canonical display formatter + enrich materializer for TV slides."""

    EMPTY = EMPTY_DISPLAY

    @classmethod
    def normalize_spec(cls, spec: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(spec, dict) or not spec.get("category"):
            return {"category": "general", "locale": "pt-BR"}
        category = str(spec.get("category") or "").strip().lower()
        if not DisplayFormatHintsService.is_valid_category(category):
            return {"category": "general", "locale": "pt-BR"}
        preset_id = str(spec.get("presetId") or "").strip()
        preset = _PRESETS.get(preset_id) if preset_id else None
        if preset and category == str(preset.get("category") or ""):
            merged = {**preset, **spec, "presetId": preset_id or spec.get("presetId")}
            merged["category"] = category
            merged["locale"] = spec.get("locale") or "pt-BR"
            return merged
        out = {"locale": "pt-BR", **spec, "category": category}
        return out

    @classmethod
    def validate_write_spec(cls, spec: Any) -> dict[str, Any]:
        """Reject invalid authored specs before normalize_spec can fall back to General."""
        if not isinstance(spec, dict):
            raise ValueError("displayFormat deve ser um objeto")
        category = spec.get("category")
        if not isinstance(category, str) or not DisplayFormatHintsService.is_valid_category(category):
            raise ValueError("category desconhecida")
        preset_id = spec.get("presetId")
        if preset_id is not None:
            if not isinstance(preset_id, str) or preset_id not in _PRESETS:
                raise ValueError("presetId desconhecido")
            if _PRESETS[preset_id]["category"] != category:
                raise ValueError("presetId incompatível com category")
        elif category == "date":
            if not isinstance(spec.get("pattern"), str) or not spec["pattern"].strip():
                raise ValueError("date exige presetId ou pattern")
        if category == "custom" and (
            not isinstance(spec.get("pattern"), str) or not spec["pattern"].strip()
        ):
            raise ValueError("custom exige pattern")
        if "decimalPlaces" in spec and spec["decimalPlaces"] is not None and (
            isinstance(spec["decimalPlaces"], bool)
            or not isinstance(spec["decimalPlaces"], int)
            or not 0 <= spec["decimalPlaces"] <= 20
        ):
            raise ValueError("decimalPlaces inválido")
        if "locale" in spec and spec["locale"] != "pt-BR":
            raise ValueError("locale não suportado")
        if "currency" in spec and spec["currency"] != "BRL":
            raise ValueError("currency não suportada")
        return dict(spec)

    @classmethod
    def spec_from_preset_id(cls, preset_id: str) -> dict[str, Any]:
        preset = _PRESETS.get(preset_id)
        if not preset:
            return {"category": "general", "locale": "pt-BR"}
        return {**preset, "presetId": preset_id, "locale": "pt-BR"}

    @classmethod
    def resolve_spec(
        cls,
        *,
        display_format: Any = None,
        legacy_format: str | None = None,
        decimal_places: Any = None,
        kind: str = "text",
    ) -> dict[str, Any]:
        if isinstance(display_format, dict) and display_format.get("category"):
            return cls.normalize_spec(display_format)
        return cls.normalize_spec(
            cls._spec_from_legacy(legacy_format, decimal_places, kind=kind)
        )

    @classmethod
    def _spec_from_legacy(
        cls,
        legacy_format: str | None,
        decimal_places: Any,
        *,
        kind: str,
    ) -> dict[str, Any]:
        token = str(legacy_format or "").strip().lower()
        places: int | None
        try:
            places = int(decimal_places) if decimal_places is not None else None
        except (TypeError, ValueError):
            places = None

        if kind == "category":
            if token == "day":
                return cls.spec_from_preset_id("date-short")
            if token == "month":
                return cls.spec_from_preset_id("date-month")
            if token == "year":
                return cls.spec_from_preset_id("date-year")
            if token == "autodate":
                return cls.spec_from_preset_id("date-auto")
            return cls.spec_from_preset_id("text")

        if token == "date":
            return cls.spec_from_preset_id("date-short")
        if token in {"raw", "plain", ""} and kind in {"text", "kpi"}:
            if token in {"raw", "plain"} or (kind == "text" and not token):
                base = cls.spec_from_preset_id("text")
                if places is not None and kind == "kpi":
                    return {"category": "text", "presetId": "text", "locale": "pt-BR"}
                return base
        if token == "percent":
            return {
                "category": "percent",
                "presetId": "percent",
                "decimalPlaces": places if places is not None else 1,
                "locale": "pt-BR",
            }
        if token in {"currency", "currency4"}:
            preset = "currency-brl-4" if token == "currency4" or places == 4 else "currency-brl"
            return {
                **cls.spec_from_preset_id(preset),
                "decimalPlaces": places
                if places is not None
                else (4 if preset == "currency-brl-4" else 2),
            }
        if token == "compact":
            return {
                **cls.spec_from_preset_id("number-compact"),
                "decimalPlaces": places if places is not None else 1,
            }
        if token == "integer":
            return cls.spec_from_preset_id("number-0")
        if token in {"number", "decimal"}:
            if places is not None:
                return {"category": "number", "decimalPlaces": places, "locale": "pt-BR"}
            if token == "decimal" or kind == "canvas":
                return {"category": "number", "locale": "pt-BR"}
            return {"category": "number", "locale": "pt-BR"}
        if token == "auto" or not token:
            return {
                "category": "general",
                "presetId": "general",
                "decimalPlaces": places,
                "locale": "pt-BR",
            }
        return {"category": "general", "presetId": "general", "locale": "pt-BR"}

    @classmethod
    def format_value(cls, value: Any, spec: dict[str, Any] | None = None) -> str:
        resolved = cls.normalize_spec(spec)
        if value is None or value == "":
            return EMPTY_DISPLAY

        category = str(resolved.get("category") or "general")
        if category == "text":
            return str(value)

        # Geral: preserve zero-padded codes (filial 01/02) — Excel-like coerce would drop zeros.
        if category == "general" and _is_zero_padded_numeric_code(value):
            return str(value).strip()

        if category == "custom":
            pattern = str(resolved.get("pattern") or "").strip()
            if not pattern:
                return _stringify_fallback(value)
            custom = format_custom_pattern(value, pattern)
            return custom if custom is not None else _stringify_fallback(value)

        if category in {"date", "time"}:
            if isinstance(value, str) and is_localized_chart_period_label(value):
                return localize_english_month_tokens_in_label(value)
            date = parse_display_date(value)
            if not date:
                return _stringify_fallback(value)
            return _format_date_spec(date, resolved, str(value))

        num = _coerce_number(value)
        if num is None:
            return _stringify_fallback(value)
        return _format_number_spec(num, resolved)

    @classmethod
    def format_catalog_entries(cls) -> list[dict[str, Any]]:
        """Canonical picker catalog (labels/patterns) — specs come from `_PRESETS`."""
        out: list[dict[str, Any]] = []
        for entry in _FORMAT_CATALOG:
            format_id = str(entry["formatId"])
            out.append(
                {
                    "formatId": format_id,
                    "category": entry["category"],
                    "label": entry["label"],
                    "pattern": entry.get("pattern"),
                    "compatibleTypes": list(entry.get("compatibleTypes") or ("any",)),
                    "spec": cls.spec_from_preset_id(format_id),
                }
            )
        return out

    @classmethod
    def reason_message(cls, reason_code: str | None) -> str | None:
        if not reason_code:
            return None
        return _REASON_MESSAGES_PT.get(str(reason_code), _REASON_MESSAGES_PT["VALUE_INVALID"])

    @classmethod
    def classify_value_presence(cls, value: Any) -> str | None:
        """Return presence reasonCode when value cannot be formatted, else None."""
        if value is None:
            return "VALUE_NULL"
        if isinstance(value, str) and value.strip() == "":
            return "VALUE_EMPTY"
        return None

    @classmethod
    def try_format_value(
        cls,
        value: Any,
        spec: dict[str, Any] | None = None,
        *,
        semantic_type: str | None = None,
    ) -> dict[str, Any]:
        """Format with explicit convertibility (no fabricated dates/NaN for picker)."""
        resolved = cls.normalize_spec(spec)
        category = str(resolved.get("category") or "general")
        format_id = str(resolved.get("presetId") or category)
        presence = cls.classify_value_presence(value)
        if presence:
            return {
                "formatId": format_id,
                "preview": None,
                "convertible": False,
                "reasonCode": presence,
                "reason": cls.reason_message(presence),
                "spec": resolved,
            }

        sem = str(semantic_type or "").strip().lower() or None
        type_block = cls._type_incompatible(category, sem, value)
        if type_block:
            return {
                "formatId": format_id,
                "preview": None,
                "convertible": False,
                "reasonCode": type_block,
                "reason": cls.reason_message(type_block),
                "spec": resolved,
            }

        if category == "text":
            return {
                "formatId": format_id,
                "preview": str(value),
                "convertible": True,
                "reasonCode": None,
                "reason": None,
                "spec": resolved,
            }

        if category == "general" and _is_zero_padded_numeric_code(value):
            return {
                "formatId": format_id,
                "preview": str(value).strip(),
                "convertible": True,
                "reasonCode": None,
                "reason": None,
                "spec": resolved,
            }

        if category == "general":
            num = _coerce_number(value)
            if num is None:
                return {
                    "formatId": format_id,
                    "preview": _stringify_fallback(value),
                    "convertible": True,
                    "reasonCode": None,
                    "reason": None,
                    "spec": resolved,
                }
            return {
                "formatId": format_id,
                "preview": _format_number_spec(num, resolved),
                "convertible": True,
                "reasonCode": None,
                "reason": None,
                "spec": resolved,
            }

        if category == "custom":
            pattern = str(resolved.get("pattern") or "").strip()
            if not pattern:
                return {
                    "formatId": format_id,
                    "preview": None,
                    "convertible": False,
                    "reasonCode": "FORMAT_UNSUPPORTED",
                    "reason": cls.reason_message("FORMAT_UNSUPPORTED"),
                    "spec": resolved,
                }
            custom = format_custom_pattern(value, pattern)
            if custom is None:
                code = (
                    "VALUE_NOT_DATE"
                    if _pattern_looks_like_date(pattern)
                    else "VALUE_NOT_NUMBER"
                )
                return {
                    "formatId": format_id,
                    "preview": None,
                    "convertible": False,
                    "reasonCode": code,
                    "reason": cls.reason_message(code),
                    "spec": resolved,
                }
            return {
                "formatId": format_id,
                "preview": custom,
                "convertible": True,
                "reasonCode": None,
                "reason": None,
                "spec": resolved,
            }

        if category in {"date", "time"}:
            if isinstance(value, str) and is_localized_chart_period_label(value):
                preview = localize_english_month_tokens_in_label(value)
                return {
                    "formatId": format_id,
                    "preview": preview,
                    "convertible": True,
                    "reasonCode": None,
                    "reason": None,
                    "spec": resolved,
                }
            date = parse_display_date(value)
            if not date:
                code = "VALUE_NOT_DATE" if category == "date" else "VALUE_NOT_TIME"
                if isinstance(value, str) and value.strip():
                    code = "PARSE_FAILED" if category == "date" else code
                return {
                    "formatId": format_id,
                    "preview": None,
                    "convertible": False,
                    "reasonCode": code,
                    "reason": cls.reason_message(code),
                    "spec": resolved,
                }
            if category == "time" and bool(date.get("dateOnly")) and not cls._has_time_parts(
                value
            ):
                # DATE-only values are not times; avoid inventing 00:00 as success for time formats
                # when semantic type is date.
                if sem in {"date"}:
                    return {
                        "formatId": format_id,
                        "preview": None,
                        "convertible": False,
                        "reasonCode": "TYPE_INCOMPATIBLE",
                        "reason": cls.reason_message("TYPE_INCOMPATIBLE"),
                        "spec": resolved,
                    }
            preview = _format_date_spec(date, resolved, str(value))
            return {
                "formatId": format_id,
                "preview": preview,
                "convertible": True,
                "reasonCode": None,
                "reason": None,
                "spec": resolved,
            }

        num = _coerce_number(value)
        if num is None:
            code = "VALUE_NOT_NUMBER"
            if isinstance(value, str) and value.strip():
                code = "PARSE_FAILED"
            return {
                "formatId": format_id,
                "preview": None,
                "convertible": False,
                "reasonCode": code,
                "reason": cls.reason_message(code),
                "spec": resolved,
            }
        return {
            "formatId": format_id,
            "preview": _format_number_spec(num, resolved),
            "convertible": True,
            "reasonCode": None,
            "reason": None,
            "spec": resolved,
        }

    @classmethod
    def _has_time_parts(cls, value: Any) -> bool:
        if not isinstance(value, str):
            return isinstance(value, (int, float))
        return bool(re.search(r"[T\s]\d{2}:\d{2}", value.strip()))

    @classmethod
    def _type_incompatible(
        cls, category: str, semantic_type: str | None, value: Any
    ) -> str | None:
        if not semantic_type or semantic_type in {"any", "unknown", "text", "string"}:
            return None
        if category in {"date"} and semantic_type in {
            "number",
            "currency",
            "percent",
            "integer",
            "float",
        }:
            # Allow numeric timestamps (unix) — only block when value is clearly non-date text.
            if isinstance(value, str) and not parse_display_date(value) and _coerce_number(value) is None:
                return "TYPE_INCOMPATIBLE"
            if isinstance(value, (int, float)):
                return None
            if parse_display_date(value):
                return None
            return "TYPE_INCOMPATIBLE"
        if category in {"number", "currency", "accounting", "percent", "scientific"} and semantic_type in {
            "date",
            "datetime",
            "time",
        }:
            if _coerce_number(value) is not None:
                return None
            return "TYPE_INCOMPATIBLE"
        return None

    @classmethod
    def preview_format_catalog(
        cls,
        *,
        value: Any = None,
        semantic_type: str | None = None,
        locale: str = "pt-BR",
        timezone: str | None = None,
        value_source: str = "authoritative",
        custom_pattern: str | None = None,
        selected_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Batch catalog + previews for one value (picker contract)."""
        _ = timezone  # reserved for DATETIME; DATE-only paths ignore TZ shifts
        options: list[dict[str, Any]] = []
        for entry in cls.format_catalog_entries():
            result = cls.try_format_value(
                value, entry["spec"], semantic_type=semantic_type
            )
            options.append(
                {
                    "formatId": entry["formatId"],
                    "category": entry["category"],
                    "label": entry["label"],
                    "pattern": entry.get("pattern"),
                    "compatibleTypes": entry["compatibleTypes"],
                    "spec": entry["spec"],
                    "preview": result.get("preview"),
                    "convertible": bool(result.get("convertible")),
                    "reasonCode": result.get("reasonCode"),
                    "reason": result.get("reason"),
                }
            )

        custom_spec = {
            "category": "custom",
            "presetId": "custom",
            "pattern": str(custom_pattern or "").strip(),
            "locale": locale or "pt-BR",
        }
        custom_result = cls.try_format_value(
            value, custom_spec, semantic_type=semantic_type
        )
        custom_option = {
            "formatId": "custom",
            "category": "custom",
            "label": "Personalizado",
            "pattern": custom_spec["pattern"] or None,
            "compatibleTypes": ["any"],
            "spec": custom_spec,
            "preview": custom_result.get("preview"),
            "convertible": bool(custom_result.get("convertible"))
            if custom_spec["pattern"]
            else False,
            "reasonCode": custom_result.get("reasonCode")
            if custom_spec["pattern"]
            else "FORMAT_UNSUPPORTED",
            "reason": custom_result.get("reason")
            if custom_spec["pattern"]
            else cls.reason_message("FORMAT_UNSUPPORTED"),
        }

        selected = None
        if isinstance(selected_spec, dict) and selected_spec.get("category"):
            selected = cls.try_format_value(
                value, selected_spec, semantic_type=semantic_type
            )
            selected = {
                **selected,
                "category": str(selected_spec.get("category") or ""),
                "label": None,
                "pattern": selected_spec.get("pattern"),
            }
        elif custom_pattern is not None and str(custom_pattern).strip():
            selected = {**custom_result, "category": "custom", "label": "Personalizado"}

        source = str(value_source or "authoritative").strip().lower()
        if source not in {"authoritative", "representative", "sample", "none"}:
            source = "authoritative"
        if cls.classify_value_presence(value) and source != "none":
            # Keep declared source; UI may still show sample badge when source=sample.
            pass

        return {
            "locale": locale or "pt-BR",
            "timezone": timezone,
            "semanticType": semantic_type,
            "valueSource": source if value is not None else "none",
            "value": value if source != "none" else None,
            "options": options,
            "custom": custom_option,
            "selected": selected,
            "categories": [
                {"category": "general", "label": "Geral"},
                {"category": "number", "label": "Número"},
                {"category": "currency", "label": "Moeda"},
                {"category": "accounting", "label": "Contábil"},
                {"category": "date", "label": "Data abreviada"},
                {"category": "time", "label": "Hora"},
                {"category": "percent", "label": "Porcentagem"},
                {"category": "scientific", "label": "Científico"},
                {"category": "text", "label": "Texto"},
                {"category": "custom", "label": "Personalizado"},
            ],
        }

    # --- field resolution (text / dataRef) ---------------------------------

    @classmethod
    def extract_field_values(cls, resolved: dict[str, Any] | None, field: str) -> list[Any]:
        if not isinstance(resolved, dict) or not str(field or "").strip():
            return []
        trimmed = str(field).strip()
        if trimmed.startswith("filter."):
            context = resolved.get("contextValues")
            if isinstance(context, dict):
                raw = context.get(trimmed)
                if raw is not None and raw != "":
                    return [raw]
            return []

        rows_raw = (
            (resolved.get("table") or {}).get("rows")
            if isinstance(resolved.get("table"), dict)
            else None
        )
        rows = [r for r in (rows_raw or []) if isinstance(r, dict)]
        columns = (
            (resolved.get("table") or {}).get("columns")
            if isinstance(resolved.get("table"), dict)
            else None
        )
        dump = cls._is_campo_valor_dump(columns)
        metric_dump = cls._is_metric_field_value_dump(columns)
        time_series = cls._is_time_series_table(columns)

        from_kpi = cls._kpi_scalar_for_field(resolved, trimmed)
        if not time_series and not dump and not metric_dump and from_kpi is not None and from_kpi != "":
            return [from_kpi]

        if rows and not dump and not metric_dump:
            from_rows = [row.get(trimmed) for row in rows if row.get(trimmed) not in (None, "")]
            if from_rows:
                return from_rows

        if from_kpi is not None and from_kpi != "":
            return [from_kpi]

        if dump:
            for row in rows:
                if str(row.get("campo") or "").strip() == trimmed:
                    valor = row.get("valor")
                    if valor is not None and valor != "":
                        return [valor]

        if metric_dump:
            for row in rows:
                if str(row.get("field") or "").strip() == trimmed:
                    valor = row.get("value")
                    # Preserve legitimate zero.
                    if valor is not None and valor != "":
                        return [valor]
                    if valor == 0 or valor == 0.0:
                        return [valor]

        if rows and trimmed in rows[0]:
            value = rows[0].get(trimmed)
            if value is not None and value != "":
                return [value]
        return []

    @classmethod
    def resolve_projected_field(
        cls,
        resolved: dict[str, Any] | None,
        field: str,
        aggregation: str = "first",
    ) -> dict[str, Any]:
        values = cls.extract_field_values(resolved, field)
        if not values:
            return {"kind": "empty", "values": []}
        agg = str(aggregation or "first").strip().lower() or "first"
        if agg == "list":
            return {"kind": "list", "values": values}
        if agg == "count":
            return {"kind": "scalar", "values": values, "scalar": len(values)}
        if agg in {"sum", "avg", "min", "max"}:
            nums = [n for n in (_coerce_number(v) for v in values) if n is not None]
            if not nums:
                return {"kind": "empty", "values": values}
            if agg == "sum":
                scalar: Any = float(sum(nums))
            elif agg == "avg":
                scalar = float(sum(nums) / len(nums))
            elif agg == "min":
                scalar = float(min(nums))
            else:
                scalar = float(max(nums))
            return {"kind": "scalar", "values": values, "scalar": scalar}
        first_num = _coerce_number(values[0])
        if first_num is not None:
            return {"kind": "scalar", "values": values, "scalar": first_num}
        return {"kind": "scalar", "values": values, "scalar": values[0]}

    @staticmethod
    def _is_campo_valor_dump(columns: Any) -> bool:
        if not isinstance(columns, list) or not columns:
            return False
        keys = {
            str(c.get("key") or "").strip()
            for c in columns
            if isinstance(c, dict)
        }
        return len(keys) == 2 and "campo" in keys and "valor" in keys

    @staticmethod
    def _is_metric_field_value_dump(columns: Any) -> bool:
        """kpiMetrics flattened as table rows (metric/field/value) — not wide data."""
        if not isinstance(columns, list) or not columns:
            return False
        keys = {
            str(c.get("key") or "").strip()
            for c in columns
            if isinstance(c, dict) and str(c.get("key") or "").strip()
        }
        return "field" in keys and "value" in keys and keys <= {
            "metric",
            "field",
            "value",
            "label",
            "indicador",
        }

    @staticmethod
    def _is_time_series_table(columns: Any) -> bool:
        if not isinstance(columns, list) or not columns:
            return False
        for col in columns:
            if not isinstance(col, dict):
                continue
            key = str(col.get("key") or "").strip().lower()
            if key in _TIME_SERIES_COLUMN_KEYS:
                return True
        return False

    @classmethod
    def _kpi_scalar_for_field(cls, resolved: dict[str, Any], field: str) -> Any:
        metrics = resolved.get("kpiMetrics")
        if isinstance(metrics, list):
            for metric in metrics:
                if isinstance(metric, dict) and str(metric.get("field") or "") == field:
                    return metric.get("value")
            for alias in _IDD_ALIASES.get(field, ()):
                for metric in metrics:
                    if isinstance(metric, dict) and str(metric.get("field") or "") == alias:
                        return metric.get("value")
        kpi = resolved.get("kpi")
        if isinstance(kpi, dict):
            if field in {"value", str(kpi.get("label") or "")}:
                return kpi.get("value")
            if field in {"score", "idd"} and kpi.get("value") not in (None, ""):
                return kpi.get("value")
        return None

    # --- enrich materialization -------------------------------------------

    @classmethod
    def apply_to_resolved(
        cls,
        resolved: dict[str, Any],
        block: dict[str, Any],
    ) -> dict[str, Any]:
        """Materialize display* strings after view projection bake."""
        if not isinstance(resolved, dict):
            return resolved
        out = dict(resolved)
        block_type = str(block.get("type") or "")

        if block_type in {"text", "heading", "shape"}:
            cls._apply_text_display(out, block)
            if block_type == "shape" and isinstance(block.get("efficiencyPin"), dict):
                cls._apply_efficiency_pin_presentation(out, block)
        elif block_type == "kpi_view":
            cls._apply_kpi_display(out, block)
            cls._apply_kpi_presentation(out, block)
        elif block_type == "table_view":
            cls._apply_table_display(out, block)
        elif block_type == "chart_view":
            cls._apply_chart_display(out, block)
        elif block_type == "canvas_table":
            cls._apply_canvas_table_display(out, block)

        out["serverDisplayApplied"] = True
        return out

    @classmethod
    def apply_canvas_table_source_map(
        cls,
        block: dict[str, Any],
        by_source: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Materialize displayRuns per linked source for canvas_table cells (G16)."""
        if not isinstance(by_source, dict) or not by_source:
            return by_source
        refs_by_source = cls._canvas_table_data_refs_by_source(block)
        out: dict[str, dict[str, Any]] = {}
        for sid, resolved in by_source.items():
            refs = refs_by_source.get(sid) or refs_by_source.get("") or []
            if not refs:
                # Still mark applied so paint knows enrich ran (fallback client OK).
                next_resolved = dict(resolved) if isinstance(resolved, dict) else {}
                next_resolved["serverDisplayApplied"] = True
                out[sid] = next_resolved
                continue
            synthetic = {
                "type": "text",
                "dataSourceId": sid,
                "contentRuns": [{"text": "", "dataRef": dict(ref)} for ref in refs],
            }
            next_resolved = cls.apply_to_resolved(dict(resolved), synthetic)
            cls._apply_canvas_display_series(next_resolved, refs)
            out[sid] = next_resolved
        return out

    @classmethod
    def _canvas_table_data_refs_by_source(
        cls, block: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        primary = str(block.get("dataSourceId") or "").strip()
        by_source: dict[str, list[dict[str, Any]]] = {}
        seen: dict[str, set[str]] = {}
        cells = block.get("cells")
        if not isinstance(cells, list):
            return by_source
        for row in cells:
            if not isinstance(row, list):
                continue
            for cell in row:
                if not isinstance(cell, dict):
                    continue
                data_ref = cell.get("dataRef")
                if not isinstance(data_ref, dict):
                    continue
                field = str(data_ref.get("field") or "").strip()
                if not field:
                    continue
                sid = str(cell.get("dataSourceId") or "").strip() or primary
                if not sid:
                    continue
                key = field
                bucket = seen.setdefault(sid, set())
                if key in bucket:
                    continue
                bucket.add(key)
                by_source.setdefault(sid, []).append(dict(data_ref))
        return by_source

    @classmethod
    def _apply_canvas_table_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        """Primary resolved: format fields used by cells pointing at block.dataSourceId."""
        primary = str(block.get("dataSourceId") or "").strip()
        refs_by_source = cls._canvas_table_data_refs_by_source(block)
        refs = refs_by_source.get(primary) or []
        if not refs:
            return
        synthetic = {
            "type": "text",
            "dataSourceId": primary,
            "contentRuns": [{"text": "", "dataRef": dict(ref)} for ref in refs],
        }
        cls._apply_text_display(resolved, synthetic)
        cls._apply_canvas_display_series(resolved, refs)

    @classmethod
    def sanitize_contradictory_text_binding(
        cls, block: dict[str, Any]
    ) -> dict[str, Any]:
        """Mutation/Campo write: single-field ``textProjection`` clears dataRefs.

        Aligns with ``textBindingOwner.consolidateTextBindingToProjection``.
        Persist never keeps ``textProjection.field`` alongside ``contentRuns[].dataRef``
        (G15 / dual-bind). Static runs without dataRef are preserved.
        """
        if not isinstance(block, dict):
            return block
        projection = block.get("textProjection")
        if not isinstance(projection, dict):
            return block
        proj_field = str(projection.get("field") or "").strip()
        if not proj_field:
            return block
        runs = block.get("contentRuns")
        if not isinstance(runs, list) or not runs:
            return block

        has_data_ref = False
        static_only: list[dict[str, Any]] = []
        for run in runs:
            if not isinstance(run, dict):
                continue
            data_ref = run.get("dataRef")
            field = (
                str(data_ref.get("field") or "").strip()
                if isinstance(data_ref, dict)
                else ""
            )
            if field:
                has_data_ref = True
                continue
            next_run = dict(run)
            next_run.pop("dataRef", None)
            static_only.append(next_run)

        if not has_data_ref:
            return block

        next_block = dict(block)
        if static_only:
            next_block["contentRuns"] = static_only
        else:
            next_block.pop("contentRuns", None)
        return next_block

    @classmethod
    def display_signals_for_verify(
        cls, resolved: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Compact display* surface for VISTA VERIFY / outcome helpers.

        Prefer these over client reformat of raw ``kpi.value`` / ISO dates.
        """
        if not isinstance(resolved, dict):
            return {}
        out: dict[str, Any] = {}
        if resolved.get("serverDisplayApplied") is True:
            out["serverDisplayApplied"] = True
        for key in ("displayText", "displayRuns"):
            if key in resolved:
                out[key] = resolved[key]
        kpi = resolved.get("kpi")
        if isinstance(kpi, dict) and isinstance(kpi.get("displayValue"), str):
            out["kpiDisplayValue"] = kpi["displayValue"]
        table = resolved.get("table")
        if isinstance(table, dict) and table.get("displayRows") is not None:
            out["tableDisplayRows"] = table.get("displayRows")
        chart = resolved.get("chart")
        if isinstance(chart, dict) and isinstance(chart.get("points"), list):
            paints = [
                {
                    k: p.get(k)
                    for k in ("displayLabel", "displayValue")
                    if isinstance(p, dict) and p.get(k) is not None
                }
                for p in chart["points"]
                if isinstance(p, dict)
            ]
            paints = [row for row in paints if row]
            if paints:
                out["chartDisplayPoints"] = paints
            if isinstance(chart.get("yAxisTicks"), list) and chart["yAxisTicks"]:
                out["yAxisTicks"] = chart["yAxisTicks"]
            if chart.get("effectiveGoal") is not None:
                out["effectiveGoal"] = chart.get("effectiveGoal")
            if isinstance(chart.get("gaugeModel"), dict):
                out["gaugeModel"] = chart["gaugeModel"]
        if isinstance(resolved.get("kpiPresentation"), dict):
            out["kpiPresentation"] = resolved["kpiPresentation"]
        if isinstance(resolved.get("efficiencyPinPresentation"), dict):
            out["efficiencyPinPresentation"] = resolved["efficiencyPinPresentation"]
        if isinstance(resolved.get("displaySeries"), dict):
            out["displaySeries"] = resolved["displaySeries"]
        return out

    @classmethod
    def _format_data_ref(
        cls,
        resolved: dict[str, Any],
        ref: dict[str, Any],
        *,
        fallback: str = EMPTY_DISPLAY,
        prefix: str = "",
        suffix: str = "",
        text_case: str | None = None,
    ) -> str:
        field = str(ref.get("field") or "").strip()
        if not field:
            return fallback
        projected = cls.resolve_projected_field(
            resolved, field, str(ref.get("aggregation") or "first")
        )
        if projected["kind"] == "empty":
            return f"{prefix}{fallback}{suffix}"
        spec = cls.resolve_spec(
            display_format=ref.get("displayFormat"),
            legacy_format=str(ref.get("format") or "") or None,
            decimal_places=ref.get("decimalPlaces"),
            kind="text",
        )
        if projected["kind"] == "list":
            parts = [cls.format_value(v, spec) for v in projected["values"]]
            core = _FIELD_LIST_JOIN.join(parts)
        else:
            raw = projected.get("scalar")
            if raw is None or raw == "":
                return f"{prefix}{fallback}{suffix}"
            core = cls.format_value(raw, spec)
        from tv_app.application.services.data.text_typography_service import (
            apply_presentation_text_case,
        )

        core = apply_presentation_text_case(core, text_case)
        return f"{prefix}{core}{suffix}"

    @classmethod
    def _resolve_run_text_case(
        cls, run: dict[str, Any], block: dict[str, Any]
    ) -> str | None:
        style = run.get("style") if isinstance(run.get("style"), dict) else {}
        case = str(style.get("textCase") or "").strip().lower()
        if case and case != "none":
            return case
        block_style = block.get("style") if isinstance(block.get("style"), dict) else {}
        case = str(block_style.get("textCase") or "").strip().lower()
        return case if case and case != "none" else None

    @classmethod
    def _apply_text_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        from tv_app.application.services.data.text_typography_service import (
            apply_presentation_text_case,
        )

        runs = block.get("contentRuns")
        has_data_runs = False
        if isinstance(runs, list):
            has_data_runs = any(
                isinstance(run, dict)
                and isinstance(run.get("dataRef"), dict)
                and str((run.get("dataRef") or {}).get("field") or "").strip()
                for run in runs
            )
        linked = bool(str(block.get("dataSourceId") or "").strip())
        empty_fallback = EMPTY_DISPLAY if linked else ""
        block_case = None
        block_style = block.get("style") if isinstance(block.get("style"), dict) else {}
        raw_case = str(block_style.get("textCase") or "").strip().lower()
        if raw_case and raw_case != "none":
            block_case = raw_case

        if has_data_runs and isinstance(runs, list):
            display_runs: list[dict[str, Any]] = []
            for run in runs:
                if not isinstance(run, dict):
                    continue
                data_ref = run.get("dataRef")
                case = cls._resolve_run_text_case(run, block)
                if isinstance(data_ref, dict) and str(data_ref.get("field") or "").strip():
                    text = cls._format_data_ref(
                        resolved,
                        data_ref,
                        fallback=empty_fallback or EMPTY_DISPLAY,
                        text_case=case,
                    )
                    display_runs.append({**run, "text": text})
                else:
                    text = apply_presentation_text_case(str(run.get("text") or ""), case)
                    display_runs.append({**run, "text": text})
            resolved["displayRuns"] = display_runs
            resolved["displayText"] = "".join(
                str(r.get("text") or "") for r in display_runs
            )
            return

        projection = block.get("textProjection")
        if isinstance(projection, dict) and str(projection.get("field") or "").strip():
            if linked:
                fallback = (
                    str(projection.get("fallback") or "").strip() or EMPTY_DISPLAY
                )
            else:
                fallback = ""
            text = cls._format_data_ref(
                resolved,
                {
                    "field": projection.get("field"),
                    "aggregation": projection.get("aggregation"),
                    "format": projection.get("format"),
                    "displayFormat": projection.get("displayFormat"),
                    "decimalPlaces": projection.get("decimalPlaces"),
                },
                fallback=fallback or EMPTY_DISPLAY,
                prefix=str(projection.get("prefix") or ""),
                suffix=str(projection.get("suffix") or ""),
                text_case=block_case,
            )
            resolved["displayText"] = text
            resolved["displayRuns"] = [{"text": text}]
            return

        # Static text: materialize when block or any run carries presentation textCase.
        needs_static_case = bool(block_case)
        if not needs_static_case and isinstance(runs, list):
            for run in runs:
                if not isinstance(run, dict):
                    continue
                if cls._resolve_run_text_case(run, block):
                    needs_static_case = True
                    break
        if needs_static_case and isinstance(runs, list) and runs:
            display_runs = []
            for run in runs:
                if not isinstance(run, dict):
                    continue
                case = cls._resolve_run_text_case(run, block)
                text = apply_presentation_text_case(str(run.get("text") or ""), case)
                display_runs.append({**run, "text": text})
            resolved["displayRuns"] = display_runs
            resolved["displayText"] = "".join(str(r.get("text") or "") for r in display_runs)
            return
        if needs_static_case:
            content = str(block.get("content") or "")
            text = apply_presentation_text_case(content, block_case)
            resolved["displayText"] = text
            resolved["displayRuns"] = [{"text": text}]

    @classmethod
    def _block_needs_text_presentation_stamp(cls, block: dict[str, Any]) -> bool:
        """True when display* must be (re)stamped for paint completeness."""
        if isinstance(block.get("resolved"), dict):
            return True
        if str(block.get("dataSourceId") or "").strip():
            return True
        projection = block.get("textProjection")
        if isinstance(projection, dict) and str(projection.get("field") or "").strip():
            return True
        block_style = block.get("style") if isinstance(block.get("style"), dict) else {}
        block_case = str(block_style.get("textCase") or "").strip().lower()
        if block_case and block_case != "none":
            return True
        runs = block.get("contentRuns")
        if isinstance(runs, list):
            for run in runs:
                if not isinstance(run, dict):
                    continue
                data_ref = run.get("dataRef")
                if isinstance(data_ref, dict) and str(data_ref.get("field") or "").strip():
                    return True
                run_style = run.get("style") if isinstance(run.get("style"), dict) else {}
                run_case = str(run_style.get("textCase") or "").strip().lower()
                if run_case and run_case != "none":
                    return True
        return False

    @classmethod
    def stamp_text_presentation_on_block(cls, block: dict[str, Any]) -> dict[str, Any]:
        """Ephemeral paint stamp: resolved.display* for text/heading/shape (no persist)."""
        if not isinstance(block, dict):
            return block
        block_type = str(block.get("type") or "")
        if block_type not in {"text", "heading", "shape"}:
            return block
        if not cls._block_needs_text_presentation_stamp(block):
            return block
        merged = dict(block)
        base = (
            dict(merged["resolved"])
            if isinstance(merged.get("resolved"), dict)
            else {}
        )
        merged["resolved"] = cls.apply_to_resolved(base, merged)
        return merged

    @classmethod
    def stamp_native_config_text_presentation(
        cls, native_config: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Stamp display* onto text-bearing blocks in a nativeConfig copy (ack/enrich)."""
        if not isinstance(native_config, dict):
            return {}
        cfg = dict(native_config)
        blocks = cfg.get("blocks")
        if not isinstance(blocks, list):
            return cfg
        cfg["blocks"] = [
            cls.stamp_text_presentation_on_block(b) if isinstance(b, dict) else b
            for b in blocks
        ]
        return cfg

    @classmethod
    def _apply_kpi_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        options = block.get("kpiOptions") if isinstance(block.get("kpiOptions"), dict) else {}
        projection = (
            block.get("kpiProjection") if isinstance(block.get("kpiProjection"), dict) else {}
        )
        metrics_cfg = projection.get("metrics") if isinstance(projection.get("metrics"), list) else []
        primary_override: dict[str, Any] = {}
        if metrics_cfg and isinstance(metrics_cfg[0], dict):
            primary_override = metrics_cfg[0]

        kpi = resolved.get("kpi")
        if isinstance(kpi, dict):
            next_kpi = dict(kpi)
            spec = cls.resolve_spec(
                display_format=primary_override.get("displayFormat")
                or options.get("displayValueFormat"),
                legacy_format=str(
                    primary_override.get("format") or options.get("valueFormat") or ""
                )
                or None,
                decimal_places=primary_override.get("decimalPlaces", options.get("decimalPlaces")),
                kind="kpi",
            )
            next_kpi["displayValue"] = cls.format_value(kpi.get("value"), spec)
            resolved["kpi"] = next_kpi

        metrics = resolved.get("kpiMetrics")
        if isinstance(metrics, list) and metrics:
            cfg_by_field = {
                str(m.get("field") or ""): m
                for m in metrics_cfg
                if isinstance(m, dict) and m.get("field")
            }
            next_metrics: list[Any] = []
            for metric in metrics:
                if not isinstance(metric, dict):
                    next_metrics.append(metric)
                    continue
                field = str(metric.get("field") or "")
                override = cfg_by_field.get(field) or {}
                spec = cls.resolve_spec(
                    display_format=override.get("displayFormat")
                    or options.get("displayValueFormat"),
                    legacy_format=str(
                        override.get("format") or options.get("valueFormat") or ""
                    )
                    or None,
                    decimal_places=override.get("decimalPlaces", options.get("decimalPlaces")),
                    kind="kpi",
                )
                next_metrics.append(
                    {**metric, "displayValue": cls.format_value(metric.get("value"), spec)}
                )
            resolved["kpiMetrics"] = next_metrics

    @classmethod
    def _sparkline_points_from_resolved(cls, resolved: dict[str, Any]) -> list[float]:
        chart = resolved.get("chart") if isinstance(resolved.get("chart"), dict) else {}
        series = chart.get("series") if isinstance(chart.get("series"), list) else []
        points: list[Any] = []
        if series and isinstance(series[0], dict) and isinstance(series[0].get("points"), list):
            points = series[0]["points"]
        elif isinstance(chart.get("points"), list):
            points = chart["points"]
        out: list[float] = []
        for point in points:
            if not isinstance(point, dict):
                continue
            n = cls._as_finite_number(point.get("value"))
            if n is not None:
                out.append(n)
        return out

    @classmethod
    def _effective_kpi_context_options(
        cls,
        options: dict[str, Any],
        resolved: dict[str, Any],
        metric_override: dict[str, Any],
    ) -> dict[str, Any]:
        """Port of resolveKpiOptionsWithAutoContext — server owns auto flags."""
        mode = str(options.get("contextMode") or "off")
        if mode != "auto":
            return dict(options)
        points = cls._sparkline_points_from_resolved(resolved)
        has_series = len(points) >= 2
        target = metric_override.get("target", options.get("target"))
        has_target = cls._as_finite_number(target) is not None
        next_opts = dict(options)
        variant = next_opts.get("variant") or "hero"
        next_opts["variant"] = variant
        icon_name = str(next_opts.get("iconName") or "").strip()
        if icon_name and next_opts.get("showIcon") is not False:
            next_opts["showIcon"] = True
        else:
            next_opts["showIcon"] = False
            next_opts["iconName"] = None
        prefer_scorecard = variant == "scorecard" or (has_target and not has_series)
        if prefer_scorecard and has_target:
            next_opts["showProgress"] = True
            next_opts["showSparkline"] = False
            next_opts["showComparison"] = True
            if next_opts.get("comparisonMode") in (None, "none"):
                next_opts["comparisonMode"] = "target"
            return next_opts
        if has_series:
            next_opts["showSparkline"] = True
            next_opts["showProgress"] = False
            next_opts["showComparison"] = True
            if next_opts.get("comparisonMode") in (None, "none"):
                next_opts["comparisonMode"] = "previous"
            return next_opts
        if has_target:
            next_opts["showProgress"] = True
            next_opts["showSparkline"] = False
            next_opts["showComparison"] = True
            if next_opts.get("comparisonMode") in (None, "none"):
                next_opts["comparisonMode"] = "target"
            return next_opts
        next_opts["showSparkline"] = False
        next_opts["showProgress"] = False
        next_opts["showComparison"] = False
        next_opts["comparisonMode"] = "none"
        return next_opts

    @classmethod
    def _format_signed_pct(cls, pct: float) -> str:
        abs_pct = abs(pct)
        text = cls.format_value(
            abs_pct,
            {
                "category": "percent",
                "presetId": "percent",
                "decimalPlaces": 1 if abs_pct >= 10 else 2,
            },
        )
        if pct > 0:
            return f"+{text}"
        if pct < 0:
            return f"−{text}"
        return text

    @classmethod
    def _apply_kpi_presentation(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        """G11/G28 — materialize kpiPresentation for paint-only MFE."""
        options_raw = (
            block.get("kpiOptions") if isinstance(block.get("kpiOptions"), dict) else {}
        )
        projection = (
            block.get("kpiProjection") if isinstance(block.get("kpiProjection"), dict) else {}
        )
        metrics_cfg = (
            projection.get("metrics") if isinstance(projection.get("metrics"), list) else []
        )
        primary_override: dict[str, Any] = {}
        if metrics_cfg and isinstance(metrics_cfg[0], dict):
            primary_override = metrics_cfg[0]
        options = cls._effective_kpi_context_options(options_raw, resolved, primary_override)
        sparkline = cls._sparkline_points_from_resolved(resolved)
        kpi = resolved.get("kpi") if isinstance(resolved.get("kpi"), dict) else {}
        numeric = cls._as_finite_number(kpi.get("value"))
        value_display = (
            kpi.get("displayValue")
            if isinstance(kpi.get("displayValue"), str)
            else EMPTY_DISPLAY
        )

        mode = (
            primary_override.get("comparisonMode")
            or options.get("comparisonMode")
            or "none"
        )
        target = primary_override.get("target", options.get("target"))
        target_n = cls._as_finite_number(target)
        higher_is_better = primary_override.get(
            "higherIsBetter", options.get("higherIsBetter", True)
        )
        show_comparison = options.get("showComparison") is True
        show_progress = options.get("showProgress") is True

        baseline: float | None = None
        vs_label = "vs período"
        if mode == "target" and target_n is not None:
            baseline = target_n
            vs_label = "vs meta"
        elif mode == "previous" and len(sparkline) >= 2:
            baseline = sparkline[-2]
            vs_label = "vs período"

        comparison_display: str | None = None
        comparison_tone: str | None = None
        if show_comparison and numeric is not None and baseline is not None and baseline != 0:
            delta_pct = ((numeric - baseline) / abs(baseline)) * 100
            favorable = delta_pct >= 0 if higher_is_better else delta_pct <= 0
            arrow = "▲" if delta_pct > 0 else "▼" if delta_pct < 0 else "●"
            label = str(options.get("comparisonLabel") or "").strip()
            comparison_display = label or f"{arrow} {cls._format_signed_pct(delta_pct)} {vs_label}"
            comparison_tone = (
                "neutral" if abs(delta_pct) < 0.05 else ("positive" if favorable else "negative")
            )
        elif show_comparison and str(options.get("comparisonLabel") or "").strip():
            comparison_display = str(options.get("comparisonLabel")).strip()
            comparison_tone = "neutral"

        progress_pct: float | None = None
        if show_progress and numeric is not None and target_n is not None and target_n != 0:
            progress_pct = (numeric / target_n) * 100

        presentation: dict[str, Any] = {
            "valueDisplay": value_display,
            "comparisonDisplay": comparison_display,
            "comparisonTone": comparison_tone,
            "progressPct": progress_pct,
            "sparklinePoints": sparkline if options.get("showSparkline") else None,
            "showComparison": show_comparison,
            "showProgress": show_progress,
            "showSparkline": options.get("showSparkline") is True,
        }
        resolved["kpiPresentation"] = presentation

    @classmethod
    def _apply_canvas_display_series(
        cls,
        resolved: dict[str, Any],
        refs: list[dict[str, Any]],
    ) -> None:
        """G10 — displaySeries[field] for canvas spark/list cells."""
        series_map: dict[str, list[float]] = {}
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            field = str(ref.get("field") or "").strip()
            if not field:
                continue
            agg = str(ref.get("aggregation") or "").strip().lower()
            # Spark cells request list aggregation or are sparkline kind.
            if agg not in {"list", "sparkline", ""} and agg != "list":
                # Still materialize list projection for any field used as spark.
                pass
            projected = cls.resolve_projected_field(resolved, field, "list")
            if projected.get("kind") != "list":
                continue
            points: list[float] = []
            for v in projected.get("values") or []:
                n = cls._as_finite_number(v)
                if n is not None:
                    points.append(n)
            if len(points) >= 2:
                series_map[field] = points[:64]
        if series_map:
            existing = (
                resolved.get("displaySeries")
                if isinstance(resolved.get("displaySeries"), dict)
                else {}
            )
            resolved["displaySeries"] = {**existing, **series_map}

    @classmethod
    def _apply_efficiency_pin_presentation(
        cls, resolved: dict[str, Any], block: dict[str, Any]
    ) -> None:
        """G25 — bands + formatted % for EfficiencyPin paint."""
        binding = block.get("efficiencyPin")
        if not isinstance(binding, dict):
            return
        work_center = str(binding.get("workCenter") or "").strip()
        match_field = (
            str(binding.get("matchField") or "work_center").strip() or "work_center"
        )
        value_field = (
            str(binding.get("valueField") or "efficiency_pct").strip() or "efficiency_pct"
        )
        bands_raw = binding.get("bands") if isinstance(binding.get("bands"), dict) else {}
        good_min = cls._as_finite_number(bands_raw.get("goodMinPct"))
        warn_min = cls._as_finite_number(bands_raw.get("warnMinPct"))
        valid_max = cls._as_finite_number(bands_raw.get("validMaxPct"))
        if good_min is None:
            good_min = 95.0
        if warn_min is None:
            warn_min = 50.0
        if valid_max is None:
            valid_max = 199.0

        rows: list[dict[str, Any]] = []
        table = resolved.get("table")
        if isinstance(table, dict) and isinstance(table.get("rows"), list):
            rows = [r for r in table["rows"] if isinstance(r, dict)]
        if not rows:
            preview = resolved.get("preview")
            if isinstance(preview, dict) and isinstance(preview.get("rows"), list):
                rows = [r for r in preview["rows"] if isinstance(r, dict)]
        if not rows and isinstance(resolved.get("data"), list):
            rows = [r for r in resolved["data"] if isinstance(r, dict)]

        row: dict[str, Any] | None = None
        target = work_center.casefold()
        if target:
            for candidate in rows:
                raw = candidate.get(match_field)
                value = str(raw).strip() if raw is not None else ""
                if value.casefold() == target:
                    row = candidate
                    break

        efficiency_pct = cls._as_finite_number(row.get(value_field) if row else None)
        appointment = cls._as_finite_number(row.get("appointment_count") if row else None)

        if not work_center:
            status = "unknown"
        elif work_center and not row and resolved:
            status = "unknown"
        elif efficiency_pct is None:
            status = "unknown"
        elif efficiency_pct < 0 or efficiency_pct > valid_max:
            status = "verify"
        elif efficiency_pct >= good_min:
            status = "good"
        elif efficiency_pct >= warn_min:
            status = "warn"
        else:
            status = "bad"

        colors = {
            "good": "#22c55e",
            "warn": "#eab308",
            "bad": "#ef4444",
            "verify": "#f97316",
            "unknown": "#94a3b8",
        }
        label = work_center or str(block.get("content") or "").strip() or "CT"
        pct_spec = {"category": "percent", "decimalPlaces": 1}
        display_pct = (
            cls.format_value(efficiency_pct, pct_spec)
            if efficiency_pct is not None
            else EMPTY_DISPLAY
        )
        resolved["efficiencyPinPresentation"] = {
            "status": status,
            "color": colors.get(status, colors["unknown"]),
            "efficiencyPct": efficiency_pct,
            "efficiencyPctDisplay": display_pct,
            "workCenter": work_center,
            "appointmentCount": appointment,
            "label": label,
            "bands": {
                "goodMinPct": good_min,
                "warnMinPct": warn_min,
                "validMaxPct": valid_max,
            },
        }

    @classmethod
    def _apply_table_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        table = resolved.get("table")
        if not isinstance(table, dict):
            return
        rows = table.get("rows")
        columns = table.get("columns")
        if not isinstance(rows, list) or not isinstance(columns, list):
            return

        options = (
            block.get("tableOptions") if isinstance(block.get("tableOptions"), dict) else {}
        )
        projection = (
            block.get("tableProjection")
            if isinstance(block.get("tableProjection"), dict)
            else {}
        )
        proj_cols = (
            projection.get("columns") if isinstance(projection.get("columns"), list) else []
        )
        proj_by_key = {
            str(c.get("key") or c.get("field") or ""): c
            for c in proj_cols
            if isinstance(c, dict)
        }
        default_spec = cls.resolve_spec(
            display_format=options.get("displayValueFormat"),
            legacy_format=str(options.get("valueFormat") or "") or None,
            kind="table",
        )

        col_specs: dict[str, dict[str, Any]] = {}
        for col in columns:
            if not isinstance(col, dict):
                continue
            key = str(col.get("key") or "").strip()
            if not key:
                continue
            override = proj_by_key.get(key) or {}
            col_specs[key] = cls.resolve_spec(
                display_format=override.get("displayFormat")
                or col.get("displayFormat")
                or options.get("displayValueFormat"),
                legacy_format=str(
                    override.get("valueFormat")
                    or col.get("valueFormat")
                    or options.get("valueFormat")
                    or ""
                )
                or None,
                kind="table",
            )

        display_rows: list[dict[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            display_row: dict[str, str] = {}
            for key, spec in col_specs.items():
                display_row[key] = cls.format_value(row.get(key), spec or default_spec)
            display_rows.append(display_row)

        next_table = dict(table)
        next_table["displayRows"] = display_rows
        resolved["table"] = next_table

    @classmethod
    def _apply_chart_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
        chart = resolved.get("chart")
        if not isinstance(chart, dict):
            return
        options = (
            block.get("chartOptions") if isinstance(block.get("chartOptions"), dict) else {}
        )
        has_value_spec = bool(
            options.get("displayValueFormat")
            or options.get("valueFormat")
            or options.get("decimalPlaces") is not None
        )
        has_category_spec = bool(
            options.get("displayCategoryFormat") or options.get("categoryLabelFormat")
        )

        value_spec = (
            cls.resolve_spec(
                display_format=options.get("displayValueFormat"),
                legacy_format=str(options.get("valueFormat") or "") or None,
                decimal_places=options.get("decimalPlaces"),
                kind="chart",
            )
            if has_value_spec
            else None
        )
        category_spec = (
            cls.resolve_spec(
                display_format=options.get("displayCategoryFormat"),
                legacy_format=str(options.get("categoryLabelFormat") or "") or None,
                kind="category",
            )
            if has_category_spec
            else None
        )

        next_chart = dict(chart)
        if has_value_spec or has_category_spec:

            def _decorate_points(points: Any) -> list[Any]:
                if not isinstance(points, list):
                    return points
                out_points: list[Any] = []
                for point in points:
                    if not isinstance(point, dict):
                        out_points.append(point)
                        continue
                    next_point = dict(point)
                    if category_spec is not None:
                        label = point.get("label")
                        if label is not None and label != "":
                            next_point["displayLabel"] = cls.format_value(label, category_spec)
                    if value_spec is not None and "value" in point:
                        next_point["displayValue"] = cls.format_value(
                            point.get("value"), value_spec
                        )
                    out_points.append(next_point)
                return out_points

            if isinstance(chart.get("points"), list):
                next_chart["points"] = _decorate_points(chart.get("points"))
            series = chart.get("series")
            if isinstance(series, list):
                next_series: list[Any] = []
                for entry in series:
                    if not isinstance(entry, dict):
                        next_series.append(entry)
                        continue
                    next_entry = dict(entry)
                    if isinstance(entry.get("points"), list):
                        next_entry["points"] = _decorate_points(entry.get("points"))
                    next_series.append(next_entry)
                next_chart["series"] = next_series

        # G24/G26/G34 — ticks + effectiveGoal; domain includes meta.
        effective_goal = cls._resolve_effective_chart_goal(options, next_chart)
        next_chart["effectiveGoal"] = effective_goal
        cls._apply_chart_axis_ticks(next_chart, value_spec, goal=effective_goal)
        chart_type = str(block.get("chartType") or next_chart.get("chartType") or "").lower()
        if chart_type == "gauge":
            next_chart["gaugeModel"] = cls._build_gauge_model(
                resolved, next_chart, options, effective_goal
            )
        resolved["chart"] = next_chart

    @classmethod
    def _resolve_effective_chart_goal(
        cls,
        options: dict[str, Any],
        chart: dict[str, Any],
    ) -> float | None:
        """G26 — manual goalLineValue > projectedGoal."""
        manual = cls._as_finite_number(options.get("goalLineValue"))
        if manual is not None:
            return manual
        return cls._as_finite_number(chart.get("projectedGoal"))

    @classmethod
    def _build_gauge_model(
        cls,
        resolved: dict[str, Any],
        chart: dict[str, Any],
        options: dict[str, Any],
        goal: float | None,
    ) -> dict[str, Any]:
        """G27 — paint-ready gauge scalars + display strings."""
        # Prefer projected series/points (selected measure) over primary source kpi.
        value = None
        for point in reversed(chart.get("points") or []):
            if isinstance(point, dict):
                value = cls._as_finite_number(point.get("value"))
                if value is not None:
                    break
        if value is None:
            for entry in chart.get("series") or []:
                if not isinstance(entry, dict):
                    continue
                for point in reversed(entry.get("points") or []):
                    if isinstance(point, dict):
                        value = cls._as_finite_number(point.get("value"))
                        if value is not None:
                            break
                if value is not None:
                    break
        if value is None:
            value = cls._as_finite_number(
                (resolved.get("kpi") or {}).get("value")
                if isinstance(resolved.get("kpi"), dict)
                else None
            )
        label = (
            str(
                (resolved.get("kpi") or {}).get("label")
                if isinstance(resolved.get("kpi"), dict)
                else ""
            ).strip()
            or str(resolved.get("label") or "").strip()
            or str(options.get("seriesName") or options.get("title") or "").strip()
            or "Valor"
        )
        title = (
            str(options.get("title") or resolved.get("label") or label).strip() or label
        )
        accent = str(options.get("seriesColor") or "").strip() or None
        import math

        value_spec = cls.resolve_spec(
            display_format=options.get("displayValueFormat"),
            legacy_format=str(options.get("valueFormat") or "") or None,
            decimal_places=options.get("decimalPlaces"),
            kind="chart",
        )
        # Infer percent / currency for gauge unit (never force % on absolute ROL).
        series_field = ""
        series = chart.get("series")
        if isinstance(series, list) and series and isinstance(series[0], dict):
            series_field = str(series[0].get("field") or "").strip().lower()
        label_l = label.lower()
        looks_percent = (
            value_spec.get("category") == "percent"
            or series_field.endswith("_pct")
            or series_field.endswith("_percent")
            or "atingimento" in label_l
            or label_l.endswith("(%)")
            or label_l.endswith("%")
        )
        money_fields = {
            "rol",
            "gross_revenue",
            "returns",
            "discounts",
            "comparable_goal",
            "goal_value",
            "reference_goal",
            "target",
            "value",
        }
        looks_currency = value_spec.get("category") == "currency" or series_field in money_fields
        if looks_percent and value_spec.get("category") != "percent":
            value_spec = {
                **value_spec,
                "category": "percent",
                "presetId": value_spec.get("presetId") or "percent",
            }
        max_from_goal = 100.0 if looks_percent or not looks_currency else 0.0
        if goal is not None and goal > 0:
            max_from_goal = max(max_from_goal, float(math.ceil(goal)))
        if max_from_goal <= 0:
            max_from_goal = 100.0
        max_from_value = max_from_goal
        if value is not None and value > max_from_goal:
            max_from_value = float(math.ceil(value))
        value_display = (
            cls.format_value(value, value_spec) if value is not None else EMPTY_DISPLAY
        )
        if looks_percent:
            unit = "" if isinstance(value_display, str) and value_display.endswith("%") else "%"
        elif looks_currency:
            unit = ""
        else:
            unit = "%"
        return {
            "value": value,
            "goal": goal,
            "min": 0.0,
            "max": max_from_value if max_from_value > 0 else 100.0,
            "label": label,
            "unit": unit,
            "accentColor": accent,
            "showTitle": options.get("showTitle") is not False,
            "title": title,
            "valueDisplay": value_display,
            "goalDisplay": cls.format_value(goal, value_spec)
            if goal is not None
            else None,
        }

    @classmethod
    def _resolve_chart_tick_values(cls, data_min: float, data_max: float, count: int = 5) -> list[float]:
        """Port of plugin-ui resolveSeriesChartTicks — semantic domain only."""
        import math

        min_v = float(data_min)
        max_v = float(data_max)
        if not math.isfinite(min_v) or not math.isfinite(max_v):
            return [0.0, 1.0]
        if min_v == max_v:
            pad = max(abs(min_v) * 0.1, 1.0)
            min_v -= pad
            max_v += pad
        span = max_v - min_v
        raw_step = span / max(count - 1, 1)
        magnitude = 10 ** math.floor(math.log10(raw_step or 1))
        step = math.ceil(raw_step / magnitude) * magnitude or 1.0
        nice_min = math.floor(min_v / step) * step
        nice_max = math.ceil(max_v / step) * step
        headroom_ratio = (nice_max - max_v) / step if step > 0 else 0.0
        if nice_max <= max_v or headroom_ratio < 0.5:
            nice_max = round(nice_max + step, 6)
        ticks: list[float] = []
        value = nice_min
        while value <= nice_max + step * 0.001:
            ticks.append(round(value, 6))
            if len(ticks) >= count + 4:
                break
            value += step
        if len(ticks) < 2:
            return [min_v, max_v]
        if ticks[0] > min_v:
            ticks.insert(0, round(ticks[0] - step, 6))
        if ticks[-1] < max_v:
            ticks.append(round(nice_max, 6))
        return ticks

    @classmethod
    def _apply_chart_axis_ticks(
        cls,
        chart: dict[str, Any],
        value_spec: dict[str, Any] | None,
        *,
        goal: float | None = None,
    ) -> None:
        values: list[float] = []
        for point in chart.get("points") or []:
            if isinstance(point, dict):
                n = cls._as_finite_number(point.get("value"))
                if n is not None:
                    values.append(n)
        for entry in chart.get("series") or []:
            if not isinstance(entry, dict):
                continue
            for point in entry.get("points") or []:
                if isinstance(point, dict):
                    n = cls._as_finite_number(point.get("value"))
                    if n is not None:
                        values.append(n)
        if goal is not None:
            values.append(goal)
        if not values:
            return
        data_min = min(values)
        data_max = max(values)
        # Match plugin-ui resolveSeriesChartValueDomain: pad to 0 when all positive/negative.
        if data_min >= 0:
            domain_min, domain_max = 0.0, data_max
        elif data_max <= 0:
            domain_min, domain_max = data_min, 0.0
        else:
            domain_min, domain_max = data_min, data_max
        tick_values = cls._resolve_chart_tick_values(domain_min, domain_max)
        spec = value_spec or {"category": "number", "decimalPlaces": 2}
        chart["yAxisTicks"] = [
            {"value": tick, "displayLabel": cls.format_value(tick, spec)} for tick in tick_values
        ]

    @staticmethod
    def _as_finite_number(value: Any) -> float | None:
        try:
            n = float(value)
        except (TypeError, ValueError):
            return None
        if n != n or n in (float("inf"), float("-inf")):  # NaN / inf
            return None
        return n
