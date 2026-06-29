from __future__ import annotations

from datetime import datetime


def validate_optional_iso_datetime(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} deve estar em formato ISO 8601 "
            f"(ex.: 2026-06-24T10:00:00-03:00). Não use texto livre nesse campo."
        ) from exc
    return text
