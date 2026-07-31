from __future__ import annotations

from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    _attach_cover_slides,
)


def test_attach_cover_slides_maps_by_playlist_id():
    playlists = [
        {"id": "a", "name": "A"},
        {"id": "b", "name": "B"},
        {"id": "c", "name": "C"},
    ]
    covers = {
        "a": {"id": "s1", "playlistId": "a", "title": "Capa A"},
        "c": {"id": "s3", "playlistId": "c", "title": "Capa C"},
    }
    out = _attach_cover_slides(playlists, covers)
    assert out[0]["coverSlide"]["title"] == "Capa A"
    assert out[1]["coverSlide"] is None
    assert out[2]["coverSlide"]["id"] == "s3"
