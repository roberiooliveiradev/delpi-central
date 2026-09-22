"""EditorFocusStore — ephemeral focus for VISTA READ Actions."""

from __future__ import annotations

from tv_app.application.services.editor_focus_store import EditorFocusStore


def test_record_and_get_for_user():
    store = EditorFocusStore(ttl_seconds=90)
    store.record(
        user_id="u1",
        playlist_id="p1",
        slide_id="s1",
        selected_ids=["b1", "b2"],
        client_id="c1",
    )
    focus = store.get_for_user("u1")
    assert focus is not None
    assert focus["playlistId"] == "p1"
    assert focus["slideId"] == "s1"
    assert focus["selectedIds"] == ["b1", "b2"]
    assert focus["stale"] is False
    assert store.get_for_user("u2") is None


def test_get_for_user_playlist_filters():
    store = EditorFocusStore(ttl_seconds=90)
    store.record(user_id="u1", playlist_id="p1", slide_id="s1", selected_ids=[])
    assert store.get_for_user_playlist("u1", "p1") is not None
    assert store.get_for_user_playlist("u1", "p2") is None


def test_ttl_expires():
    store = EditorFocusStore(ttl_seconds=30)
    store.record(user_id="u1", playlist_id="p1", slide_id="s1")
    with store._lock:
        store._by_user["u1"]["_mono"] = 0.0  # force stale
    assert store.get_for_user("u1") is None


def test_clear_playlist_for_user():
    store = EditorFocusStore(ttl_seconds=90)
    store.record(user_id="u1", playlist_id="p1", slide_id="s1")
    store.clear_playlist_for_user("u1", "p1")
    assert store.get_for_user("u1") is None
