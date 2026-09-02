from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    counter_set_min,
)

COUNTER_RAW_KEY = "counterRaw"
COUNTER_OFFSET_KEY = "counterOffset"
_INTERNAL_METRIC_KEYS = frozenset({COUNTER_RAW_KEY, COUNTER_OFFSET_KEY})
_DEFAULT_INTENTIONAL_DECREASE_COMMANDS = frozenset({"decrement", "reset", "set"})
_DEFAULT_INTENTIONAL_DECREASE_GRACE_MS = 15_000


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


def _counter_restore_section(driver_key: str) -> dict[str, Any]:
    definition = get_device_driver_registry().resolve_driver(driver_key).definition
    section = definition.get("counterRestore")
    return section if isinstance(section, dict) else {}


def public_metrics(metrics: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        return {}
    return {key: value for key, value in metrics.items() if key not in _INTERNAL_METRIC_KEYS}


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def counter_floor() -> int:
    """Piso canônico do contador (mesmo limite do comando ``set``)."""
    return counter_set_min()


def intentional_decrease_command_keys(driver_key: str) -> frozenset[str]:
    """Comandos de auditoria que explicam uma queda intencional no chip."""
    section = _counter_restore_section(driver_key)
    raw = section.get("intentionalDecreaseCommands")
    if not isinstance(raw, list) or not raw:
        return _DEFAULT_INTENTIONAL_DECREASE_COMMANDS
    keys = {str(item).strip().lower() for item in raw if str(item).strip()}
    return frozenset(keys) if keys else _DEFAULT_INTENTIONAL_DECREASE_COMMANDS


def intentional_decrease_command_grace_ms(driver_key: str) -> int:
    """Janela em que um comando recente autoriza aceitar queda no poll."""
    section = _counter_restore_section(driver_key)
    raw = section.get("intentionalDecreaseCommandGraceMs", _DEFAULT_INTENTIONAL_DECREASE_GRACE_MS)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_INTENTIONAL_DECREASE_GRACE_MS
    return max(0, value)


def is_unexplained_counter_drop(prev_raw: int, new_raw: int) -> bool:
    """Queda de raw sem provenance de comando — candidata a power-loss/restore."""
    return new_raw < prev_raw


def _apply_counter_floor(
    *,
    logical: int,
    raw_val: int,
    offset: int,
    meta: dict[str, Any],
) -> tuple[int, int, int]:
    """Garante contador lógico/raw >= piso; zera offset se o raw veio negativo."""
    floor = counter_floor()
    if logical >= floor and raw_val >= floor:
        return logical, raw_val, offset
    meta["counter_floored"] = True
    meta["counter_floor"] = floor
    meta["counter_floor_from_logical"] = logical
    meta["counter_floor_from_raw"] = raw_val
    if raw_val < floor:
        return floor, floor, 0
    return max(floor, logical), raw_val, offset


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

    ``accept_decrease``: provenance de comando (decrement/reset/set) ou path de comando —
    nunca trata queda como power-loss. No poll sem comando recente, qualquer queda restaura.
    Contagem nunca fica abaixo do piso canônico (``counterSet.min``, tipicamente 0).
    """
    previous = previous_metrics if isinstance(previous_metrics, dict) else {}
    result = dict(raw_metrics)
    meta: dict[str, Any] = {}

    if clear_offsets:
        for key in _monotonic_metric_keys(driver_key):
            raw_val = _as_int(raw_metrics.get(key))
            if raw_val is None:
                continue
            logical, stored_raw, offset = _apply_counter_floor(
                logical=raw_val,
                raw_val=raw_val,
                offset=0,
                meta=meta,
            )
            result[key] = logical
            result[COUNTER_RAW_KEY] = stored_raw
            result[COUNTER_OFFSET_KEY] = offset
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
            logical, stored_raw, offset = _apply_counter_floor(
                logical=raw_val,
                raw_val=raw_val,
                offset=0,
                meta=meta,
            )
            result[key] = logical
            result[COUNTER_RAW_KEY] = stored_raw
            result[COUNTER_OFFSET_KEY] = offset
            continue

        power_loss = (not accept_decrease) and is_unexplained_counter_drop(prev_raw, raw_val)
        if power_loss:
            # Hardware perdeu a contagem (power-loss / reboot). Mantém continuidade lógica.
            offset = prev_logical
            logical = raw_val + offset
            logical, stored_raw, offset = _apply_counter_floor(
                logical=logical,
                raw_val=raw_val,
                offset=offset,
                meta=meta,
            )
            result[key] = logical
            result[COUNTER_RAW_KEY] = stored_raw
            result[COUNTER_OFFSET_KEY] = offset
            meta["counter_restored"] = True
            meta["counter_restore_mode"] = "software_offset"
            meta["counter_restore_from"] = prev_logical
            meta["counter_restore_raw"] = raw_val
            meta["counter_restore_reason"] = "unexplained_drop"
        else:
            # Provenance de comando (ou incremento): mantém offset e acompanha o raw.
            logical = raw_val + prev_offset
            logical, stored_raw, offset = _apply_counter_floor(
                logical=logical,
                raw_val=raw_val,
                offset=prev_offset,
                meta=meta,
            )
            result[key] = logical
            result[COUNTER_RAW_KEY] = stored_raw
            result[COUNTER_OFFSET_KEY] = offset
            if accept_decrease and is_unexplained_counter_drop(prev_raw, raw_val):
                meta["counter_decrease_accepted"] = True
                meta["counter_decrease_provenance"] = "recent_command"

    return result, meta


def build_hardware_set_payload(*, counter: int) -> dict[str, Any]:
    return {"counter": int(counter)}


def counter_restore_enabled(driver_key: str) -> bool:
    section = _counter_restore_section(driver_key)
    if not section:
        return True
    return bool(section.get("enabled", True))


__all__ = [
    "COUNTER_OFFSET_KEY",
    "COUNTER_RAW_KEY",
    "apply_monotonic_continuity",
    "build_hardware_set_payload",
    "counter_floor",
    "counter_restore_enabled",
    "intentional_decrease_command_grace_ms",
    "intentional_decrease_command_keys",
    "is_unexplained_counter_drop",
    "public_metrics",
]
