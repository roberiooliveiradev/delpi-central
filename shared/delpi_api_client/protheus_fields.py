"""Helpers para campos Protheus normalizados (Fase 5) com fallback legado."""

from __future__ import annotations

from typing import Any


def coerce_yes_no(value: Any, *, default: bool | None = None) -> bool | None:
    """Aceita bool normalizado ou string SIM/NAO legada."""
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return default

    normalized = value.strip().upper()
    if normalized in {"SIM", "SIM_SC2"}:
        return True
    if normalized in {"NAO", "NÃO"}:
        return False
    return default


def read_yes_no_label(payload: dict[str, Any], field: str) -> str | None:
    label_key = f"{field}_label"
    label = payload.get(label_key)
    if isinstance(label, str) and label.strip():
        return label.strip()

    parsed = coerce_yes_no(payload.get(field))
    if parsed is True:
        return "Sim"
    if parsed is False:
        return "Não"
    return None
