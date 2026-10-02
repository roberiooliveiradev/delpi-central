from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tv_app.infrastructure.cache.single_flight import SingleFlightRegistry
from tv_app.infrastructure.cache.ttl_cache import TtlCache

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_settings.json"


@lru_cache(maxsize=1)
def _load_settings() -> dict[str, Any]:
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def native_data_cache_ttl_seconds() -> float:
    cache_cfg = _load_settings().get("nativeDataCache") or {}
    return float(cache_cfg.get("ttlSeconds") or 120)


def native_data_cache_retention_seconds() -> float:
    """Physical entry lifetime. Must cover the largest legitimate consumer
    max-age (playlist globalRefreshSec max = 3600)."""
    cache_cfg = _load_settings().get("nativeDataCache") or {}
    return float(cache_cfg.get("retentionSeconds") or 3600)


def native_data_cache_max_entries() -> int:
    """Hard bound on in-memory entries — retention extension (3600s) is only
    safe while the cache is size-bounded."""
    cache_cfg = _load_settings().get("nativeDataCache") or {}
    return int(cache_cfg.get("maxEntries") or 1024)


def build_native_data_cache_key(
    *,
    screen_key: str,
    config: dict[str, Any] | None,
    authorization: str | None,
) -> str:
    cfg = config or {}
    auth_scope = "user" if authorization else "service"
    return json.dumps(
        {
            "screenKey": screen_key,
            "config": cfg,
            "authScope": auth_scope,
        },
        sort_keys=True,
        default=str,
    )


_native_cache = TtlCache[dict[str, Any]](
    ttl_seconds=native_data_cache_ttl_seconds(),
    retention_seconds=native_data_cache_retention_seconds(),
    max_entries=native_data_cache_max_entries(),
)
# Single-flight por processo: mesma native cache key em voo ⇒ um único resolve downstream.
_native_inflight = SingleFlightRegistry[dict[str, Any]]()


def get_cached_native_data(
    key: str, *, max_age_seconds: float | None = None
) -> dict[str, Any] | None:
    return _native_cache.get(key, max_age_seconds=max_age_seconds)


def set_cached_native_data(key: str, value: dict[str, Any]) -> None:
    if value.get("error"):
        return
    _native_cache.set(key, value)


def get_native_inflight() -> SingleFlightRegistry[dict[str, Any]]:
    return _native_inflight


def reset_native_data_cache() -> None:
    _native_cache.invalidate_all()
    _native_inflight.invalidate_all()


def native_data_cache_stats() -> dict[str, float | int]:
    return _native_cache.stats()
