# app/tests/test_app_usage_live_store.py

from app.infrastructure.app_usage.in_memory_app_usage_live_store import (
    InMemoryAppUsageLiveStore,
)


def test_live_store_groups_sessions_by_app():
    store = InMemoryAppUsageLiveStore(ttl_seconds=90)

    store.bind_session(user_id="user-1", session_id="s1")
    store.bind_session(user_id="user-2", session_id="s2")

    store.set_active_app("s1", app_id="dashboard-lmps", route_path="/lmps")
    store.set_active_app("s2", app_id="dashboard-lmps", route_path="/lmps/v2")

    live_apps = store.list_live_apps()

    assert len(live_apps) == 1
    assert live_apps[0].app_id == "dashboard-lmps"
    assert live_apps[0].user_count == 2
    assert live_apps[0].session_count == 2


def test_live_store_touch_keeps_app_active():
    store = InMemoryAppUsageLiveStore(ttl_seconds=90)

    store.bind_session(user_id="user-1", session_id="s1")
    store.set_active_app("s1", app_id="minha-delpi-chat")
    store.touch("s1", app_id="minha-delpi-chat")

    sessions = store.list_live_sessions()

    assert len(sessions) == 1
    assert sessions[0].app_id == "minha-delpi-chat"
