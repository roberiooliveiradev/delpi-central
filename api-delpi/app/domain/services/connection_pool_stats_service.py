"""Estatísticas dos connection pools da api-delpi (Plugins Postgres + TOTVS)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection_pool,
)
from app.infrastructure.providers.totvs.connection_pool import (
    TOTVS_POOL_ACQUIRE_TIMEOUT,
    TOTVS_POOL_ENABLED,
    TOTVS_POOL_MAX_SIZE,
    get_totvs_connection_pool,
)


def build_connection_pool_stats_payload(
    *,
    plugins: dict[str, Any],
    totvs: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "plugins_postgres": plugins,
        "totvs": totvs,
    }


def _totvs_disabled_stats() -> dict[str, Any]:
    return {
        "enabled": False,
        "max_size": TOTVS_POOL_MAX_SIZE,
        "created": 0,
        "available": 0,
        "in_use": 0,
        "acquire_timeout_seconds": TOTVS_POOL_ACQUIRE_TIMEOUT,
        "acquire_timeouts_total": 0,
        "discards_total": 0,
    }


def enrich_pool_stats_with_occupancy(pool: dict[str, Any]) -> dict[str, Any]:
    """Add occupancy_pct = in_use / max_size (0 when pool disabled or empty max)."""
    max_size = int(pool.get("max_size") or 0)
    in_use = int(pool.get("in_use") or 0)
    occupancy_pct = round((100.0 * in_use / max_size), 2) if max_size > 0 else 0.0
    return {**pool, "occupancy_pct": occupancy_pct}


def get_connection_pool_stats_summary() -> dict[str, Any]:
    plugins = enrich_pool_stats_with_occupancy(get_plugins_connection_pool().stats())
    totvs_pool = get_totvs_connection_pool()
    if totvs_pool is None or not TOTVS_POOL_ENABLED:
        totvs = enrich_pool_stats_with_occupancy(_totvs_disabled_stats())
    else:
        totvs = enrich_pool_stats_with_occupancy(totvs_pool.stats())
    return build_connection_pool_stats_payload(plugins=plugins, totvs=totvs)


def get_connection_pools_glance() -> dict[str, Any]:
    """Compact pool view for console-health glance (RED saturation)."""
    summary = get_connection_pool_stats_summary()
    plugins = summary["plugins_postgres"]
    totvs = summary["totvs"]
    candidates: list[float] = []
    if plugins.get("enabled"):
        candidates.append(float(plugins.get("occupancy_pct") or 0.0))
    if totvs.get("enabled"):
        candidates.append(float(totvs.get("occupancy_pct") or 0.0))
    return {
        "captured_at": summary["captured_at"],
        "plugins_postgres": plugins,
        "totvs": totvs,
        "max_occupancy_pct": max(candidates) if candidates else 0.0,
    }
