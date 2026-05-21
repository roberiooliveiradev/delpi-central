from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def row_to_json(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None

    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


def rows_to_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row_to_json(row) or {} for row in rows]
