from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

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
    build_mock.assert_called_once_with("valid-token", track_view=True)
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
