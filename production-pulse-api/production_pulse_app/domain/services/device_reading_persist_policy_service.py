from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from production_pulse_app.infrastructure.content.telemetry_persistence_content_service import (
    always_persist_meta_keys,
    deadband_for_metric,
    heartbeat_ms,
)

# R46–R48: quando persistir reading de poll/manual.


@dataclass(frozen=True)
class PersistReadingDecision:
    should_persist: bool
    reason: str


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metrics_changed_beyond_deadband(
    *,
    role_key: str,
    previous_metrics: dict[str, Any] | None,
    new_metrics: dict[str, Any] | None,
) -> bool:
    previous = previous_metrics if isinstance(previous_metrics, dict) else {}
    current = new_metrics if isinstance(new_metrics, dict) else {}
    if not current:
        return False
    if not previous:
        return True

    keys = set(previous.keys()) | set(current.keys())
    for key in keys:
        new_num = _numeric(current.get(key))
        prev_num = _numeric(previous.get(key))
        if new_num is None and prev_num is None:
            if previous.get(key) != current.get(key):
                return True
            continue
        if new_num is None or prev_num is None:
            return True
        delta = abs(new_num - prev_num)
        if delta == 0:
            continue
        threshold = deadband_for_metric(role_key, key, default=0.0)
        if threshold <= 0 or delta >= threshold:
            return True
    return False


def _meta_requires_persist(meta: dict[str, Any] | None) -> bool:
    if not isinstance(meta, dict) or not meta:
        return False
    keys = always_persist_meta_keys()
    return any(meta.get(key) is True for key in keys)


def decide_persist_reading(
    *,
    source: str,
    role_key: str,
    previous_metrics: dict[str, Any] | None,
    new_metrics: dict[str, Any] | None,
    last_persisted_at: datetime | None,
    now: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> PersistReadingDecision:
    """R46–R48 — command sempre; poll/manual sob deadband + heartbeat."""
    normalized_source = str(source or "").strip().lower()
    if normalized_source == "command":
        return PersistReadingDecision(True, "command")

    if _meta_requires_persist(meta):
        return PersistReadingDecision(True, "restore_or_reset")

    if last_persisted_at is None:
        return PersistReadingDecision(True, "first")

    if metrics_changed_beyond_deadband(
        role_key=role_key,
        previous_metrics=previous_metrics,
        new_metrics=new_metrics,
    ):
        return PersistReadingDecision(True, "change")

    current = now or datetime.now(timezone.utc)
    current_utc = _as_utc(current) or datetime.now(timezone.utc)
    last_utc = _as_utc(last_persisted_at)
    if last_utc is None:
        return PersistReadingDecision(True, "first")

    elapsed_ms = (current_utc - last_utc).total_seconds() * 1000.0
    if elapsed_ms >= heartbeat_ms(role_key):
        return PersistReadingDecision(True, "heartbeat")

    return PersistReadingDecision(False, "skipped_unchanged")
