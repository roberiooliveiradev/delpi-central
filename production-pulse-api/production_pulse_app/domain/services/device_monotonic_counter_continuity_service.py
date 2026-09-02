from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)

COUNTER_RAW_KEY = "counterRaw"
COUNTER_OFFSET_KEY = "counterOffset"
_INTERNAL_METRIC_KEYS = frozenset({COUNTER_RAW_KEY, COUNTER_OFFSET_KEY})
_DEFAULT_MAX_INTENTIONAL_DECREASE = 50


def _monotonic_metric_keys(driver_key: str) -> frozenset[str]:
    definition = get_device_driver_registry().resolve_driver(driver_key).definition
    metrics = definition.get("metrics") or []
    keys: set[str] = set()
    if isinstance(metrics, list):
        for metric in metrics:
            if isinstance(metric, dict) and metric.get("monotonic"):
                key = str(metric.get("key") or "").strip()
                if key:
                    keys.add(key)
    return frozenset(keys)


def public_metrics(metrics: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        return {}
    return {key: value for key, value in metrics.items() if key not in _INTERNAL_METRIC_KEYS}


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def max_intentional_decrease(driver_key: str) -> int:
    """Quedas até este valor (ex.: −1 do pad) não são power-loss."""
    definition = get_device_driver_registry().resolve_driver(driver_key).definition
    section = definition.get("counterRestore")
    if not isinstance(section, dict):
        return _DEFAULT_MAX_INTENTIONAL_DECREASE
    raw = section.get("maxIntentionalDecrease", _DEFAULT_MAX_INTENTIONAL_DECREASE)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_INTENTIONAL_DECREASE
    return max(0, value)


def is_power_loss_counter_drop(
    prev_raw: int,
    new_raw: int,
    *,
    max_intentional_decrease: int,
) -> bool:
    """True só quando a queda parece reboot/perda de RAM — não −1/−N do operador."""
    if new_raw >= prev_raw:
        return False
    return (prev_raw - new_raw) > max_intentional_decrease


def apply_monotonic_continuity(
    *,
    driver_key: str,
    previous_metrics: dict[str, Any] | None,
    raw_metrics: dict[str, Any],
    clear_offsets: bool = False,
    accept_decrease: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normaliza métricas monotônicas com offset após perda de memória no hardware.

    Retorna (metrics_para_persistir, meta). ``counter`` fica lógico (visível);
    ``counterRaw`` / ``counterOffset`` ficam só no last_metrics interno.

    ``accept_decrease``: comandos increment/decrement — nunca trata queda como power-loss.
    """
    previous = previous_metrics if isinstance(previous_metrics, dict) else {}
    result = dict(raw_metrics)
    meta: dict[str, Any] = {}
    intentional_cap = max_intentional_decrease(driver_key)

    if clear_offsets:
        for key in _monotonic_metric_keys(driver_key):
            raw_val = _as_int(raw_metrics.get(key))
            if raw_val is None:
                continue
            result[key] = raw_val
            result[COUNTER_RAW_KEY] = raw_val
            result[COUNTER_OFFSET_KEY] = 0
        return result, meta

    for key in _monotonic_metric_keys(driver_key):
        raw_val = _as_int(raw_metrics.get(key))
        if raw_val is None:
            continue

        prev_logical = _as_int(previous.get(key))
        prev_raw = _as_int(previous.get(COUNTER_RAW_KEY))
        if prev_raw is None and prev_logical is not None:
            prev_raw = prev_logical
        prev_offset = _as_int(previous.get(COUNTER_OFFSET_KEY)) or 0

        if prev_logical is None or prev_raw is None:
            result[key] = raw_val
            result[COUNTER_RAW_KEY] = raw_val
            result[COUNTER_OFFSET_KEY] = 0
            continue

        power_loss = (not accept_decrease) and is_power_loss_counter_drop(
            prev_raw,
            raw_val,
            max_intentional_decrease=intentional_cap,
        )
        if power_loss:
            # Hardware perdeu a contagem (power-loss / reboot). Mantém continuidade lógica.
            offset = prev_logical
            logical = raw_val + offset
            result[key] = logical
            result[COUNTER_RAW_KEY] = raw_val
            result[COUNTER_OFFSET_KEY] = offset
            meta["counter_restored"] = True
            meta["counter_restore_mode"] = "software_offset"
            meta["counter_restore_from"] = prev_logical
            meta["counter_restore_raw"] = raw_val
        else:
            # Inclui −1 do pad / botão físico: mantém offset e acompanha o raw.
            logical = raw_val + prev_offset
            result[key] = logical
            result[COUNTER_RAW_KEY] = raw_val
            result[COUNTER_OFFSET_KEY] = prev_offset

    return result, meta


def build_hardware_set_payload(*, counter: int) -> dict[str, Any]:
    return {"counter": int(counter)}


def counter_restore_enabled(driver_key: str) -> bool:
    definition = get_device_driver_registry().resolve_driver(driver_key).definition
    section = definition.get("counterRestore")
    if not isinstance(section, dict):
        return True
    return bool(section.get("enabled", True))


__all__ = [
    "COUNTER_OFFSET_KEY",
    "COUNTER_RAW_KEY",
    "apply_monotonic_continuity",
    "build_hardware_set_payload",
    "counter_restore_enabled",
    "is_power_loss_counter_drop",
    "max_intentional_decrease",
    "public_metrics",
]
