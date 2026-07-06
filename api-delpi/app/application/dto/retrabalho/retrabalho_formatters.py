from __future__ import annotations

from typing import Any


def round_hours(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 4)


def round_cost(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def display_operador_nome(value: Any) -> str:
    normalized = clean_text(value)
    return normalized or "Sem nome cadastrado"
