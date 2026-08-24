"""Merge de overrides MP-OK / CT após refresh do TOTVS."""

from __future__ import annotations

from typing import Any


def empty_overrides() -> dict[str, dict[str, Any]]:
    return {}


def merge_overrides_after_refresh(
    *,
    previous_overrides: dict[str, Any] | None,
    order_keys: set[str],
) -> dict[str, dict[str, Any]]:
    """Preserva overrides só das OPs que ainda existem no dump novo."""
    if not isinstance(previous_overrides, dict):
        return empty_overrides()

    merged: dict[str, dict[str, Any]] = {}
    for production_order, raw in previous_overrides.items():
        key = str(production_order or "").strip()
        if not key or key not in order_keys or not isinstance(raw, dict):
            continue
        merged[key] = {
            "mp_ok": bool(raw.get("mp_ok")),
            "work_center": str(raw.get("work_center") or "").strip(),
        }
    return merged


def apply_override_patch(
    overrides: dict[str, dict[str, Any]],
    *,
    production_order: str,
    mp_ok: bool | None = None,
    work_center: str | None = None,
) -> dict[str, dict[str, Any]]:
    key = str(production_order or "").strip()
    if not key:
        return overrides

    current = dict(overrides.get(key) or {"mp_ok": False, "work_center": ""})
    if mp_ok is not None:
        current["mp_ok"] = bool(mp_ok)
    if work_center is not None:
        current["work_center"] = str(work_center).strip()
    updated = dict(overrides)
    updated[key] = current
    return updated


def apply_override_updates(
    overrides: dict[str, dict[str, Any]],
    updates: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result = dict(overrides)
    for raw in updates:
        if not isinstance(raw, dict):
            continue
        production_order = str(raw.get("production_order") or "").strip()
        if not production_order:
            continue
        result = apply_override_patch(
            result,
            production_order=production_order,
            mp_ok=raw.get("mp_ok") if "mp_ok" in raw else None,
            work_center=raw.get("work_center") if "work_center" in raw else None,
        )
    return result
