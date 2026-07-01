from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID


def json_safe(value: Any) -> Any:
    """Converte valores de linha PG para tipos serializáveis em JSON."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def row_to_json(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return json_safe(dict(row))


def rows_to_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row_to_json(row) or {} for row in rows]
