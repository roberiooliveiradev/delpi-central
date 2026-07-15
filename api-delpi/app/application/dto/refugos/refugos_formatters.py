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


def format_protheus_date(value: Any) -> str:
    """Converte YYYYMMDD → YYYY-MM-DD quando possível."""
    raw = clean_text(value)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw
