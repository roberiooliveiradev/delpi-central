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


def test_realtime_hub_relays_slide_draft():
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        hub._rooms["playlist-1"] = {FakeWebSocket()}  # noqa: SLF001
        await hub._handle_message(  # noqa: SLF001
            FakeWebSocket(),
            playlist_id="playlist-1",
            message=(
                '{"type":"slide_draft","clientId":"editor-1","slideId":"slide-a",'
                '"nativeConfig":{"body":"texto ao vivo"}}'
            ),
        )
        assert sent[0]["type"] == "slide_draft"
        assert sent[0]["slideId"] == "slide-a"
        assert sent[0]["clientId"] == "editor-1"
        assert sent[0]["nativeConfig"] == {"body": "texto ao vivo"}

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


def test_public_presentation_ws_broadcasts_editor_presence():
    client = TestClient(app)
    playlist = {
        "id": "00000000-0000-0000-0000-000000000001",
        "publicToken": "tok-presence",
        "isActive": True,
    }
    with patch(
        "tv_app.interface.http.routes.presentation_realtime_routes._repo.get_by_token",
        return_value=playlist,
    ):
        with client.websocket_connect("/public/present/tok-presence/ws") as first:
            assert first.receive_json()["type"] == "connected"
            first.send_json(
                {
                    "type": "presence_join",
                    "clientId": "editor-1",
                    "displayName": "Ana",
                    "role": "editor",
                }
            )
            assert first.receive_json() == {
                "type": "presence_update",
                "playlistId": playlist["id"],
                "peers": [
                    {
                        "clientId": "editor-1",
                        "displayName": "Ana",
                        "role": "editor",
                    }
                ],
            }

            with client.websocket_connect("/public/present/tok-presence/ws") as second:
                assert second.receive_json()["type"] == "connected"
                second.send_json(
                    {
                        "type": "presence_join",
                        "clientId": "editor-2",
                        "displayName": "Bruno",
                        "role": "editor",
                    }
                )
                peers = first.receive_json()["peers"]
                assert {peer["clientId"] for peer in peers} == {"editor-1", "editor-2"}
                assert second.receive_json()["type"] == "presence_update"

                second.send_json({"type": "presence_leave", "clientId": "editor-2"})
                assert first.receive_json()["peers"] == [
                    {
                        "clientId": "editor-1",
                        "displayName": "Ana",
                        "role": "editor",
                    }
                ]


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
