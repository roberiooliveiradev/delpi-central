from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.interface.http.routes import media_routes


def test_list_media_returns_items():
    playlist_id = uuid4()
    asset_id = uuid4()
    repo = MagicMock()
    repo.list_for_playlist.return_value = [
        {
            "id": str(asset_id),
            "playlistId": str(playlist_id),
            "storedName": "file.png",
            "originalName": "banner.png",
            "mimeType": "image/png",
            "mediaKind": "image",
            "fileSizeBytes": 1200,
            "createdBy": "user",
            "createdAt": "2026-07-07T12:00:00",
        }
    ]
    media_routes._media_repo = repo

    class User:
        is_superadmin = True
        sub = "admin-1"

    request = MagicMock()
    request.state = MagicMock()
    request.state.user = User()

    with patch(
        "tv_app.interface.http.playlist_access_http._access.resolve",
        return_value=PlaylistAccess(
            level="owner",
            playlist={"id": str(playlist_id), "publicToken": "tok", "isActive": True},
        ),
    ):
        response = media_routes.list_media(request, playlist_id)
    body = response.body.decode("utf-8")
    assert '"success":true' in body.replace(" ", "")
    assert str(asset_id) in body
    repo.list_for_playlist.assert_called_once_with(playlist_id, media_kind=None)
