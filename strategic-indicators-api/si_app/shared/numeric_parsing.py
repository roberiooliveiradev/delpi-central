"""Parse numérico seguro — blank/inválido → None (não float(''))."""

from __future__ import annotations


def to_optional_float(value: object) -> float | None:
    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def optional_float_map(
    values: dict[str, object] | None,
) -> dict[str, float | None]:
    if not values:
        return {}
    return {key: to_optional_float(value) for key, value in values.items()}
