from __future__ import annotations

from typing import Any

from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    END_KEYS,
    PERIOD_DAYS_KEY,
    START_KEYS,
)


def _has_value(layer: dict[str, Any], key: str) -> bool:
    value = layer.get(key)
    return value is not None and value != ""


def input_overrides_period_intent(input_overrides: dict[str, Any] | None) -> bool:
    """True se a camada de input/runtime fixa período (datas ou periodDays)."""
    if not isinstance(input_overrides, dict):
        return False
    if _has_value(input_overrides, PERIOD_DAYS_KEY):
        return True
    return any(_has_value(input_overrides, key) for key in (*START_KEYS, *END_KEYS))


def reconcile_merged_params_after_input(
    merged: dict[str, Any],
    *,
    input_overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Input/runtime vence preset relativo e periodDays/datas da fonte.

    Sem isso, `dateRangePreset: this_month` em dataBinding.params recalcula o mês
    inteiro e ignora filtro interativo (Data fim / Período dias).
    """
    if not input_overrides_period_intent(input_overrides):
        return merged
    out = dict(merged)
    overrides = input_overrides if isinstance(input_overrides, dict) else {}
    out.pop(DATE_RANGE_PRESET_KEY, None)
    has_explicit_dates = any(_has_value(overrides, key) for key in (*START_KEYS, *END_KEYS))
    has_period_days = _has_value(overrides, PERIOD_DAYS_KEY)
    if has_explicit_dates and not has_period_days:
        # Datas do filtro não podem ser recalculadas por periodDays da fonte.
        out.pop(PERIOD_DAYS_KEY, None)
    if has_period_days and not has_explicit_dates:
        # last_n a partir do input: remove datas concretas herdadas da fonte.
        for key in (*START_KEYS, *END_KEYS):
            if not _has_value(overrides, key):
                out.pop(key, None)
    return out


def merge_data_params(
    *,
    playlist_defaults: dict[str, Any] | None,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
    input_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """playlist → slide → bloco → inputs/runtime (mais específico ganha)."""
    merged: dict[str, Any] = {}
    for layer in (playlist_defaults, slide_filters, block_params, input_overrides):
        if not isinstance(layer, dict):
            continue
        for key, value in layer.items():
            if value is None or value == "":
                continue
            merged[str(key)] = value
    return reconcile_merged_params_after_input(merged, input_overrides=input_overrides)


def param_inherited_from_slide(
    key: str,
    *,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
) -> bool:
    slide = slide_filters if isinstance(slide_filters, dict) else {}
    block = block_params if isinstance(block_params, dict) else {}
    return key in slide and key not in block
