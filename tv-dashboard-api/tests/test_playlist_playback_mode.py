"""Contrato playbackMode na playlist / payload de apresentação."""

from tv_app.infrastructure.persistence.repositories.playlist_repository import _row_to_playlist


def test_row_to_playlist_maps_playback_mode():
    row = {
        "id": "00000000-0000-0000-0000-000000000001",
        "public_token": "tok",
        "name": "P",
        "description": None,
        "viewport_profile": "1080p",
        "viewport_width": None,
        "viewport_height": None,
        "transition_style": "fade",
        "default_duration_sec": 30,
        "playback_mode": "meeting",
        "global_refresh_sec": 300,
        "is_active": True,
        "view_count": 0,
        "last_presented_at": None,
        "created_by": "u1",
        "owner_user_id": "u1",
        "created_at": None,
        "updated_at": None,
        "revision": 1,
        "data_defaults": {},
        "master_config": {},
    }
    playlist = _row_to_playlist(row)
    assert playlist["playbackMode"] == "meeting"


def test_row_to_playlist_defaults_playback_mode_when_missing():
    row = {
        "id": "00000000-0000-0000-0000-000000000002",
        "public_token": "tok2",
        "name": "P2",
        "description": None,
        "viewport_profile": "1080p",
        "viewport_width": None,
        "viewport_height": None,
        "transition_style": "fade",
        "default_duration_sec": 30,
        "global_refresh_sec": 300,
        "is_active": True,
        "view_count": 0,
        "last_presented_at": None,
        "created_by": "u1",
        "owner_user_id": "u1",
        "created_at": None,
        "updated_at": None,
        "revision": 0,
        "data_defaults": {},
        "master_config": {},
    }
    playlist = _row_to_playlist(row)
    assert playlist["playbackMode"] == "presentation"


def test_update_playlist_body_accepts_playback_mode():
    from tv_app.interface.http.routes.playlist_routes import UpdatePlaylistBody

    body = UpdatePlaylistBody(playbackMode="meeting")
    assert body.playbackMode == "meeting"
