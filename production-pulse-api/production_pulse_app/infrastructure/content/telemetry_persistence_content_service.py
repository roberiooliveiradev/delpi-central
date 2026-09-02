from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "telemetry_persistence.json"


@lru_cache(maxsize=1)
def load_telemetry_persistence_catalog() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def reset_telemetry_persistence_catalog_cache() -> None:
    load_telemetry_persistence_catalog.cache_clear()


def _defaults() -> dict[str, Any]:
    catalog = load_telemetry_persistence_catalog()
    section = catalog.get("defaults")
    return section if isinstance(section, dict) else {}


def _role_section(role_key: str) -> dict[str, Any]:
    catalog = load_telemetry_persistence_catalog()
    by_role = catalog.get("byRoleKey")
    if not isinstance(by_role, dict):
        return {}
    section = by_role.get(str(role_key or "").strip())
    return section if isinstance(section, dict) else {}


def heartbeat_ms(role_key: str, *, default: int = 30_000) -> int:
    role = _role_section(role_key)
    raw = role.get("heartbeatMs", _defaults().get("heartbeatMs", default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1_000, value)


def raw_retention_days(*, default: int = 90) -> int:
    raw = _defaults().get("rawRetentionDays", default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, value)


def deadband_for_metric(role_key: str, metric_key: str, *, default: float = 0.0) -> float:
    role = _role_section(role_key)
    deadband = role.get("deadband")
    if not isinstance(deadband, dict):
        deadband = _defaults().get("deadband")
    if not isinstance(deadband, dict):
        return default
    raw = deadband.get(metric_key)
    if raw is None and metric_key == "counter":
        raw = _defaults().get("counterDeadband", default)
    try:
        return abs(float(raw))
    except (TypeError, ValueError):
        return default


def always_persist_meta_keys() -> frozenset[str]:
    catalog = load_telemetry_persistence_catalog()
    raw = catalog.get("alwaysPersistMetaKeys")
    if not isinstance(raw, list):
        return frozenset({"counter_restored", "counter_reset", "counter_decreased"})
    return frozenset(str(item).strip() for item in raw if str(item).strip())


def rollup_enabled(*, default: bool = True) -> bool:
    raw = _defaults().get("rollupEnabled", default)
    return bool(raw)
