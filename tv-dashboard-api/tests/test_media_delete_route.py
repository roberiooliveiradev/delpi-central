from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tv_app.application.services.media_storage_service import MediaStorageService
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.interface.http.routes import media_routes


def _owner_access(playlist_id):
    return PlaylistAccess(
        level="owner",
        playlist={"id": str(playlist_id), "publicToken": "tok", "isActive": True},
    )


def _request_user(*, is_superadmin: bool = True):
    class User:
        def __init__(self):
            self.is_superadmin = is_superadmin
            self.sub = "admin-1"

    request = MagicMock()
    request.state = MagicMock()
    request.state.user = User()
    return request


def test_delete_media_removes_db_row_and_file(tmp_path: Path):
    playlist_id = uuid4()
    asset_id = uuid4()
    stored_name = "clip.mp4"
    file_path = tmp_path / stored_name
    file_path.write_bytes(b"0123456789")

    asset = {
        "id": str(asset_id),
        "playlistId": str(playlist_id),
        "storedName": stored_name,
        "originalName": "Inicio.mp4",
        "mimeType": "video/mp4",
        "mediaKind": "video",
        "fileSizeBytes": 10,
        "createdBy": "user",
        "createdAt": "2026-07-30T12:00:00",
    }
    repo = MagicMock()
    repo.delete.return_value = asset
    media_routes._media_repo = repo
    media_routes._storage = MediaStorageService(base_dir=str(tmp_path))

    request = _request_user()
    with (
        patch(
            "tv_app.interface.http.playlist_access_http._access.resolve",
            return_value=_owner_access(playlist_id),
        ),
        patch("tv_app.interface.http.routes.media_routes.notify_presentation_changed") as notify,
    ):
        response = media_routes.delete_media(request, playlist_id, asset_id)

    body = response.body.decode("utf-8")
    assert response.status_code == 200
    assert '"success":true' in body.replace(" ", "")
    assert '"deleted":true' in body.replace(" ", "")
    assert "Mídia excluída" in body or "mediaDeleted" in body or "exclu" in body.lower()
    repo.delete.assert_called_once_with(playlist_id, asset_id)
    assert not file_path.exists()
    notify.assert_called_once()
    assert notify.call_args.kwargs["reason"] == "media_deleted"


def test_delete_media_not_found():
    playlist_id = uuid4()
    asset_id = uuid4()
    repo = MagicMock()
    repo.delete.return_value = None
    media_routes._media_repo = repo
    media_routes._storage = MagicMock()

    request = _request_user()
    with patch(
        "tv_app.interface.http.playlist_access_http._access.resolve",
        return_value=_owner_access(playlist_id),
    ):
        response = media_routes.delete_media(request, playlist_id, asset_id)

    assert response.status_code == 404
    media_routes._storage.delete.assert_not_called()


def test_delete_media_requires_edit_access():
    playlist_id = uuid4()
    asset_id = uuid4()
    repo = MagicMock()
    media_routes._media_repo = repo
    media_routes._storage = MagicMock()

    request = _request_user(is_superadmin=False)
    with patch(
        "tv_app.interface.http.playlist_access_http._access.resolve",
        return_value=PlaylistAccess(
            level="viewer",
            playlist={"id": str(playlist_id), "publicToken": "tok", "isActive": True},
        ),
    ):
        response = media_routes.delete_media(request, playlist_id, asset_id)

    assert response.status_code in {403, 401}
    repo.delete.assert_not_called()
