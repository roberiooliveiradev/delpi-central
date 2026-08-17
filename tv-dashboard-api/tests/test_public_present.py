import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from tv_app.infrastructure.persistence.repositories.media_repository import MediaRepository
from tv_app.main import app


def test_public_present_not_found():
    client = TestClient(app)
    with patch(
        "tv_app.interface.http.routes.public_routes._present.build_by_token",
        return_value=None,
    ):
        response = client.get("/public/present/invalid-token")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False


def test_public_present_ok():
    client = TestClient(app)
    payload = {
        "playlist": {"id": "p1", "name": "Demo", "viewportProfile": "1080p", "transitionStyle": "fade", "globalRefreshSec": 300, "defaultDurationSec": 30},
        "slides": [],
    }
    with patch(
        "tv_app.interface.http.routes.public_routes._present.build_by_token",
        return_value=payload,
    ) as build_mock:
        response = client.get("/public/present/valid-token")
    build_mock.assert_called_once_with(
        "valid-token",
        track_view=True,
        filter_overrides=None,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["playlist"]["name"] == "Demo"


def test_build_by_token_tracks_view_when_requested():
    from tv_app.application.services.presentation_payload_service import PresentationPayloadService

    repo = MagicMock()
    repo.get_by_token.return_value = {
        "id": "00000000-0000-0000-0000-000000000001",
        "isActive": True,
        "publicToken": "tok",
        "defaultDurationSec": 30,
    }
    repo.list_slides.return_value = []
    service = PresentationPayloadService(repository=repo, native_data=MagicMock())
    with patch.object(service, "_assemble_payload", return_value={"slides": []}):
        service.build_by_token("tok", track_view=True)
    repo.touch_view.assert_called_once_with("tok")


def test_get_for_token_does_not_require_playlist_active():
    source = inspect.getsource(MediaRepository.get_for_token)
    assert "p.is_active" not in source
    assert "is_active = TRUE" not in source
    assert "public_token" in source
    assert "WHERE ma.id = %s AND p.public_token = %s" in source

def test_public_media_serves_file_without_jwt(tmp_path: Path):
    asset_id = uuid4()
    media = tmp_path / "cover.png"
    media.write_bytes(b"\x89PNG\r\n\x1a\n")
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.public_routes._media_repo.get_for_token",
            return_value={"storedName": "cover.png", "mimeType": "image/png"},
        ) as get_mock,
        patch(
            "tv_app.interface.http.routes.public_routes._storage.resolve_path",
            return_value=media,
        ),
    ):
        response = client.get(f"/public/present/tok-inativo/media/{asset_id}")
    get_mock.assert_called_once()
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_public_media_not_found_when_token_or_file_missing():
    client = TestClient(app)
    with patch(
        "tv_app.interface.http.routes.public_routes._media_repo.get_for_token",
        return_value=None,
    ):
        response = client.get(f"/public/present/tok/media/{uuid4()}")
    assert response.status_code == 404
