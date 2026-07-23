from __future__ import annotations

from tv_app.middleware.media_access_token import resolve_media_query_authorization

_ASSET = "11111111-1111-1111-1111-111111111111"
_PLAYLIST = "22222222-2222-2222-2222-222222222222"
_MEDIA_PATH = f"/playlists/{_PLAYLIST}/media/{_ASSET}"


def test_resolve_media_query_authorization_injects_bearer():
    assert (
        resolve_media_query_authorization(
            path=_MEDIA_PATH,
            method="GET",
            access_token="jwt-abc",
            existing_authorization=None,
        )
        == "Bearer jwt-abc"
    )


def test_resolve_media_query_authorization_keeps_existing_header():
    assert (
        resolve_media_query_authorization(
            path=_MEDIA_PATH,
            method="GET",
            access_token="from-query",
            existing_authorization="Bearer from-header",
        )
        is None
    )


def test_resolve_media_query_authorization_ignores_non_media_paths():
    assert (
        resolve_media_query_authorization(
            path=f"/playlists/{_PLAYLIST}",
            method="GET",
            access_token="jwt-abc",
            existing_authorization=None,
        )
        is None
    )


def test_resolve_media_query_authorization_ignores_post():
    assert (
        resolve_media_query_authorization(
            path=_MEDIA_PATH,
            method="POST",
            access_token="jwt-abc",
            existing_authorization=None,
        )
        is None
    )
