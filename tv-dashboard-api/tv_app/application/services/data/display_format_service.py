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

_DATE_HINT = re.compile(r"dd|yyyy|aaaa|mmm|HH|hh|ss|yy", re.IGNORECASE)
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
    "date-long": {"category": "date", "presetId": "date-long"},
    "date-iso": {
        "category": "date",
        "presetId": "date-iso",
        "pattern": "yyyy-mm-dd",
    },
    "date-day-mon": {"category": "date", "presetId": "date-day-mon"},
    "date-month": {"category": "date", "presetId": "date-month"},
    "date-year": {"category": "date", "presetId": "date-year"},
    "date-auto": {"category": "date", "presetId": "date-auto"},
    "time-hhmm": {"category": "time", "pattern": "HH:mm"},
    "percent": {"category": "percent", "decimalPlaces": 1},
    "scientific": {"category": "scientific", "decimalPlaces": 2},
    "text": {"category": "text"},
    "custom": {"category": "custom", "pattern": ""},
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
        return format_custom_pattern(raw, pattern) or raw

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
        time_series = cls._is_time_series_table(columns)

        from_kpi = cls._kpi_scalar_for_field(resolved, trimmed)
        if not time_series and not dump and from_kpi is not None and from_kpi != "":
            return [from_kpi]

        if rows and not dump:
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
        elif block_type == "kpi_view":
            cls._apply_kpi_display(out, block)
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
            out[sid] = cls.apply_to_resolved(dict(resolved), synthetic)
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
        return f"{prefix}{core}{suffix}"

    @classmethod
    def _apply_text_display(cls, resolved: dict[str, Any], block: dict[str, Any]) -> None:
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

        if has_data_runs and isinstance(runs, list):
            display_runs: list[dict[str, Any]] = []
            for run in runs:
                if not isinstance(run, dict):
                    continue
                data_ref = run.get("dataRef")
                if isinstance(data_ref, dict) and str(data_ref.get("field") or "").strip():
                    text = cls._format_data_ref(
                        resolved, data_ref, fallback=empty_fallback or EMPTY_DISPLAY
                    )
                    display_runs.append({**run, "text": text})
                else:
                    display_runs.append(dict(run))
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
            )
            resolved["displayText"] = text
            resolved["displayRuns"] = [{"text": text}]

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
        if not has_value_spec and not has_category_spec:
            return

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
                    next_point["displayValue"] = cls.format_value(point.get("value"), value_spec)
                out_points.append(next_point)
            return out_points

        next_chart = dict(chart)
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
        resolved["chart"] = next_chart
