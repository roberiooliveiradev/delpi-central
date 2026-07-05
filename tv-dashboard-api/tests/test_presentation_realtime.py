from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tv_app.application.services.presentation_realtime_hub import PresentationRealtimeHub
from tv_app.main import app


def test_realtime_hub_broadcasts_to_room():
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        hub._rooms["playlist-1"] = {FakeWebSocket()}  # noqa: SLF001
        await hub.broadcast_now(
            "playlist-1",
            {"type": "presentation_updated", "reason": "slide_updated"},
        )
        assert sent[0]["type"] == "presentation_updated"

    asyncio.run(_run())


def test_public_presentation_ws_ping():
    client = TestClient(app)
    playlist = {
        "id": "00000000-0000-0000-0000-000000000001",
        "publicToken": "tok-live",
        "isActive": True,
    }
    with patch(
        "tv_app.interface.http.routes.presentation_realtime_routes._repo.get_by_token",
        return_value=playlist,
    ):
        with client.websocket_connect("/public/present/tok-live/ws") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "connected"
            ws.send_text("ping")
            pong = ws.receive_json()
            assert pong["type"] == "pong"


def test_public_presentation_ws_rejects_invalid_token():
    client = TestClient(app)
    with patch(
        "tv_app.interface.http.routes.presentation_realtime_routes._repo.get_by_token",
        return_value=None,
    ):
        with pytest.raises(Exception):
            with client.websocket_connect("/public/present/invalid/ws"):
                pass


def test_admin_presentation_ws_requires_token():
    client = TestClient(app)
    playlist_id = "00000000-0000-0000-0000-000000000001"
    with patch(
        "tv_app.interface.http.routes.presentation_realtime_routes._repo.get_by_id",
        return_value={"id": playlist_id},
    ):
        with pytest.raises(Exception):
            with client.websocket_connect(f"/playlists/{playlist_id}/presentation-ws"):
                pass
