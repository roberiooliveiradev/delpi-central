# app/infrastructure/presence/presence_store_provider.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.domain.ports.user_presence_store_port import UserPresenceStorePort
from app.infrastructure.presence.in_memory_user_presence_store import (
    InMemoryUserPresenceStore,
)

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

_store: UserPresenceStorePort | None = None


def get_user_presence_store(app: Flask | None = None) -> UserPresenceStorePort:
    global _store

    if _store is not None:
        return _store

    from flask import current_app

    flask_app = app or current_app

    ttl_seconds = int(flask_app.config.get("USER_PRESENCE_TTL_SECONDS", 90))
    backend = str(flask_app.config.get("USER_PRESENCE_STORE", "memory")).strip().lower()
    redis_url = str(flask_app.config.get("REDIS_URL", "") or "").strip()

    if backend == "redis" and redis_url:
        try:
            from app.infrastructure.presence.redis_user_presence_store import (
                RedisUserPresenceStore,
            )

            _store = RedisUserPresenceStore(redis_url=redis_url, ttl_seconds=ttl_seconds)
            logger.info("User presence store: redis")
            return _store
        except Exception as exc:
            logger.warning(
                "User presence redis unavailable, using memory: %s",
                exc,
            )

    _store = InMemoryUserPresenceStore(ttl_seconds=ttl_seconds)
    logger.info("User presence store: memory")
    return _store


def reset_user_presence_store() -> None:
    global _store
    _store = None


def is_user_presence_enabled(app: Flask | None = None) -> bool:
    from flask import current_app

    flask_app = app or current_app
    return bool(flask_app.config.get("USER_PRESENCE_ENABLED", True))
