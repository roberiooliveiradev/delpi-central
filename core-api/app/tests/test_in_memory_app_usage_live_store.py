# app/tests/test_in_memory_app_usage_live_store.py

from datetime import datetime, timedelta

from app.infrastructure.app_usage.in_memory_app_usage_live_store import (
    InMemoryAppUsageLiveStore,
)


def test_pop_active_segment_returns_and_clears_app():
    store = InMemoryAppUsageLiveStore(ttl_seconds=90)
    store.bind_session(user_id="user-1", session_id="sid-1")
    store.set_active_app("sid-1", app_id="commercial", route_path="/apps/commercial")

    segment = store.pop_active_segment("sid-1")

    assert segment is not None
    assert segment["user_id"] == "user-1"
    assert segment["app_id"] == "commercial"
    assert segment["route_path"] == "/apps/commercial"
    assert segment["ended_at"] >= segment["started_at"]

    assert store.pop_active_segment("sid-1") is None


def test_collect_stale_segments_flushes_expired_sessions():
    store = InMemoryAppUsageLiveStore(ttl_seconds=30)
    store.bind_session(user_id="user-1", session_id="sid-1")
    store.set_active_app("sid-1", app_id="commercial")

    stale_time = datetime.utcnow() - timedelta(seconds=120)
    store._by_session["sid-1"].last_seen_at = stale_time
    store._by_session["sid-1"].app_connected_at = stale_time

    segments = store.collect_stale_segments(now=datetime.utcnow())

    assert len(segments) == 1
    assert segments[0]["app_id"] == "commercial"
    assert "sid-1" not in store._by_session
