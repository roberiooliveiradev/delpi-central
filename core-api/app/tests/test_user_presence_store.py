# app/tests/test_user_presence_store.py

from datetime import datetime, timedelta

from app.infrastructure.presence.in_memory_user_presence_store import (
    InMemoryUserPresenceStore,
)


def test_register_and_list_single_user():
    store = InMemoryUserPresenceStore(ttl_seconds=90)

    store.register(user_id="user-1", session_id="sid-a")
    online = store.list_online()

    assert len(online) == 1
    assert online[0].user_id == "user-1"
    assert online[0].connection_count == 1


def test_multiple_sessions_count_connections():
    store = InMemoryUserPresenceStore(ttl_seconds=90)

    store.register(user_id="user-1", session_id="sid-a")
    store.register(user_id="user-1", session_id="sid-b")

    online = store.list_online()
    assert online[0].connection_count == 2


def test_unregister_removes_user_when_last_session_gone():
    store = InMemoryUserPresenceStore(ttl_seconds=90)

    store.register(user_id="user-1", session_id="sid-a")
    store.unregister("sid-a")

    assert store.list_online() == []


def test_stale_session_is_pruned():
    store = InMemoryUserPresenceStore(ttl_seconds=1)
    store.register(user_id="user-1", session_id="sid-a")

    state = store._by_session["sid-a"]
    state.last_seen_at = datetime.utcnow() - timedelta(seconds=5)

    assert store.list_online() == []
