# app/infrastructure/app_usage/app_usage_live_store_provider.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.domain.ports.app_usage_live_store_port import AppUsageLiveStorePort
from app.infrastructure.app_usage.in_memory_app_usage_live_store import (
    InMemoryAppUsageLiveStore,
)

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

_store: AppUsageLiveStorePort | None = None


def get_app_usage_live_store(app: Flask | None = None) -> AppUsageLiveStorePort:
    global _store

    if _store is not None:
        return _store

    from flask import current_app

    flask_app = app or current_app
    ttl_seconds = int(flask_app.config.get("APP_USAGE_TTL_SECONDS", 90))
    backend = str(flask_app.config.get("APP_USAGE_STORE", "memory")).strip().lower()
    redis_url = str(flask_app.config.get("REDIS_URL", "") or "").strip()

    if backend == "redis" and redis_url:
        try:
            from app.infrastructure.app_usage.redis_app_usage_live_store import (
                RedisAppUsageLiveStore,
            )

            _store = RedisAppUsageLiveStore(redis_url=redis_url, ttl_seconds=ttl_seconds)
            logger.info("App usage live store: redis")
            return _store
        except Exception as exc:
            logger.warning(
                "App usage redis unavailable, using memory: %s",
                exc,
            )

    _store = InMemoryAppUsageLiveStore(ttl_seconds=ttl_seconds)
    logger.info("App usage live store: memory")
    return _store


def reset_app_usage_live_store() -> None:
    global _store
    _store = None


def is_app_usage_enabled(app: Flask | None = None) -> bool:
    from flask import current_app

    flask_app = app or current_app
    return bool(flask_app.config.get("APP_USAGE_ENABLED", True))
