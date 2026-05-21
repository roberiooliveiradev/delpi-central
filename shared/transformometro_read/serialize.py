from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.date().isoformat() if value.tzinfo is None else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bool):
        return value
    return value


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: serialize_value(val) for key, val in row.items()}
