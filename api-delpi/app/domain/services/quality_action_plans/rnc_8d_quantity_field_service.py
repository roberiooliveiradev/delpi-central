from __future__ import annotations

import re
from typing import Any

QUANTITY_UNIT_FIELD_PAIRS: tuple[tuple[str, str], ...] = (
    ("defective_quantity", "defective_quantity_unit"),
    ("batch_quantity", "batch_quantity_unit"),
    ("rejected_quantity", "rejected_quantity_unit"),
)

_COMBINED_QTY_UNIT_PATTERN = re.compile(
    r"^\s*(?P<qty>[\d]+(?:[.,]\d+)?)\s*(?P<unit>.+?)?\s*$",
    re.UNICODE,
)


def _parse_numeric_quantity(raw: object | None) -> int | float | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    normalized = text.replace(",", ".")
    try:
        number = float(normalized)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def split_quantity_and_unit(raw: object | None) -> tuple[int | float | None, str | None]:
    if raw is None:
        return None, None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw, None
    text = str(raw).strip()
    if not text:
        return None, None
    match = _COMBINED_QTY_UNIT_PATTERN.match(text)
    if not match:
        return None, text
    qty = _parse_numeric_quantity(match.group("qty"))
    unit = (match.group("unit") or "").strip() or None
    if qty is None and unit:
        return None, text
    return qty, unit


def format_quantity_and_unit(
    quantity: object | None,
    unit: object | None,
    *,
    legacy_combined: object | None = None,
) -> str | None:
    qty = _parse_numeric_quantity(quantity)
    unit_text = str(unit).strip() if unit is not None else ""
    if qty is not None:
        qty_text = str(int(qty)) if isinstance(qty, float) and qty.is_integer() else str(qty)
        return f"{qty_text} {unit_text}".strip() if unit_text else qty_text
    if legacy_combined is not None and str(legacy_combined).strip():
        return str(legacy_combined).strip()
    return unit_text or None


def resolve_quantity_display(payload: dict[str, Any], quantity_key: str, unit_key: str) -> str | None:
    return format_quantity_and_unit(
        payload.get(quantity_key),
        payload.get(unit_key),
        legacy_combined=payload.get(quantity_key),
    )


def normalize_template_payload_quantity_fields(payload: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(payload or {})
    for quantity_key, unit_key in QUANTITY_UNIT_FIELD_PAIRS:
        if result.get(unit_key):
            parsed_qty = _parse_numeric_quantity(result.get(quantity_key))
            if parsed_qty is not None:
                result[quantity_key] = parsed_qty
            continue
        qty, unit = split_quantity_and_unit(result.get(quantity_key))
        if qty is not None:
            result[quantity_key] = qty
        if unit:
            result[unit_key] = unit
    return result
