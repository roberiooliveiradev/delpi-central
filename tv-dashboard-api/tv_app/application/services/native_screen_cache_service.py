from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tv_app.infrastructure.cache.ttl_cache import TtlCache

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_settings.json"


@lru_cache(maxsize=1)
def _load_settings() -> dict[str, Any]:
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def native_data_cache_ttl_seconds() -> float:
    cache_cfg = _load_settings().get("nativeDataCache") or {}
    return float(cache_cfg.get("ttlSeconds") or 120)


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


_native_cache = TtlCache[dict[str, Any]](ttl_seconds=native_data_cache_ttl_seconds())


def get_cached_native_data(key: str) -> dict[str, Any] | None:
    return _native_cache.get(key)


def set_cached_native_data(key: str, value: dict[str, Any]) -> None:
    if value.get("error"):
        return
    _native_cache.set(key, value)


def reset_native_data_cache() -> None:
    _native_cache.invalidate_all()
