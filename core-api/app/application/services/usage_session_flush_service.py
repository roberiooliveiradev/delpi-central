# app/application/services/usage_session_flush_service.py

from __future__ import annotations

from datetime import datetime

from app.application.services.usage_session_recorder import persist_usage_segment
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)


def flush_stale_usage_sessions() -> int:
    flushed = 0
    now = datetime.utcnow()

    if is_app_usage_enabled():
        store = get_app_usage_live_store()
        collect = getattr(store, "collect_stale_segments", None)
        if callable(collect):
            for segment in collect(now=now):
                persist_usage_segment(
                    user_id=segment["user_id"],
                    app_id=segment.get("app_id"),
                    route_path=segment.get("route_path"),
                    started_at=segment["started_at"],
                    ended_at=segment["ended_at"],
                    source="ttl_flush",
                    socket_session_id=segment.get("socket_session_id"),
                )
                flushed += 1

    if is_user_presence_enabled():
        presence = get_user_presence_store()
        collect = getattr(presence, "collect_stale_connections", None)
        if callable(collect):
            for connection in collect(now=now):
                persist_usage_segment(
                    user_id=connection["user_id"],
                    app_id=None,
                    route_path=None,
                    started_at=connection["started_at"],
                    ended_at=connection["ended_at"],
                    source="ttl_flush",
                    socket_session_id=connection.get("socket_session_id"),
                )
                flushed += 1

    return flushed
