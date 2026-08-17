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


def get_connection_pool_stats_summary() -> dict[str, Any]:
    plugins = get_plugins_connection_pool().stats()
    totvs_pool = get_totvs_connection_pool()
    if totvs_pool is None or not TOTVS_POOL_ENABLED:
        totvs = _totvs_disabled_stats()
    else:
        totvs = totvs_pool.stats()
    return build_connection_pool_stats_payload(plugins=plugins, totvs=totvs)
