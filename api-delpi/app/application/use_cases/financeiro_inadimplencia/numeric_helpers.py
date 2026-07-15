from __future__ import annotations

from decimal import Decimal
from typing import Any


def as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float, Decimal)):
        return int(value)
    text = str(value).strip().replace(",", ".")
    return int(float(text))


def as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return round(float(value), 2)
    text = str(value).strip().replace(",", ".")
    return round(float(text), 2)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return int(value) == 1
    text = as_str(value).lower()
    return text in {"1", "true", "sim", "s", "y", "yes"}


def as_iso_date(value: Any) -> str:
    if value is None or value == "":
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    text = as_str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def safe_percent(numerator: float | int, denominator: float | int) -> float:
    if not denominator:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 2)


def build_pagination(
    *,
    page: int,
    page_size: int,
    total_items: int,
) -> dict[str, int | bool]:
    total_pages = (
        max((total_items + page_size - 1) // page_size, 1) if total_items else 1
    )
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
