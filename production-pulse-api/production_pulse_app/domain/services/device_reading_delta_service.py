from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)


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


def compute_delta_metrics(
    *,
    driver_key: str,
    previous_metrics: dict[str, Any] | None,
    new_metrics: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    previous = previous_metrics or {}
    monotonic_keys = _monotonic_metric_keys(driver_key)
    delta: dict[str, Any] = {}
    meta: dict[str, Any] = {}

    for key in monotonic_keys:
        if key not in new_metrics:
            continue
        new_val = new_metrics[key]
        if not isinstance(new_val, (int, float)) or isinstance(new_val, bool):
            continue
        new_num = int(new_val)

        prev_raw = previous.get(key)
        if prev_raw is None:
            delta[key] = 0
            continue

        prev_num = int(prev_raw)
        if new_num >= prev_num:
            delta[key] = new_num - prev_num
        else:
            delta[key] = new_num
            meta["counter_reset"] = True

    return delta, meta
