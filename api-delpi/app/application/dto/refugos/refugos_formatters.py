from __future__ import annotations

from typing import Any


def round_cost(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def round_qty(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 4)


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def display_label(value: Any, *, fallback: str) -> str:
    normalized = clean_text(value)
    return normalized or fallback


def format_code_dash_label(
    code: Any,
    description: Any,
    *,
    empty_fallback: str = "",
) -> str:
    """Monta ``SIGLA - significado``; evita duplicar quando descrição = código."""
    code_s = clean_text(code)
    desc_s = clean_text(description)
    if code_s and desc_s and desc_s.casefold() != code_s.casefold():
        return f"{code_s} - {desc_s}"
    if code_s:
        return code_s
    if desc_s:
        return desc_s
    return empty_fallback


def format_protheus_date(value: Any) -> str:
    """Converte YYYYMMDD → YYYY-MM-DD quando possível."""
    raw = clean_text(value)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw
