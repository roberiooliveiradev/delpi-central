from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "period_aggregation.json"


@lru_cache(maxsize=1)
def load_period_aggregation_catalog() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def period_timezone_name() -> str:
    catalog = load_period_aggregation_catalog()
    return str(catalog.get("timezone") or "America/Sao_Paulo")


def period_shift_windows() -> list[dict[str, Any]]:
    catalog = load_period_aggregation_catalog()
    shifts = catalog.get("shifts")
    if not isinstance(shifts, list):
        return []
    return [item for item in shifts if isinstance(item, dict)]


def monotonic_metrics_for_role(role_key: str) -> list[str]:
    catalog = load_period_aggregation_catalog()
    metrics_by_role = catalog.get("metricsByRole") or {}
    if not isinstance(metrics_by_role, dict):
        return []
    raw = metrics_by_role.get(role_key) or []
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]
