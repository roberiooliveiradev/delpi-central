from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tv_app.application.services.presentation_realtime_hub import PresentationRealtimeHub
from tv_app.application.services.presentation_realtime_models import (
    PresentationRealtimeSession,
)
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

        websocket = FakeWebSocket()
        hub._rooms["playlist-1"] = {websocket}  # noqa: SLF001
        hub._sessions[websocket] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-1",
            display_name="Ana",
            role="editor",
            can_edit=True,
        )
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-1"}',
        )
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            websocket,
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


def test_realtime_hub_relays_selection_with_server_identity():
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        websocket = FakeWebSocket()
        hub._rooms["playlist-1"] = {websocket}  # noqa: SLF001
        hub._sessions[websocket] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-1",
            display_name="Ana Silva",
            role="editor",
            can_edit=True,
        )
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-1","displayName":"Falso"}',
        )
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message=(
                '{"type":"selection_update","clientId":"editor-1","slideId":"slide-a",'
                '"selectedIds":["block-1","block-2"]}'
            ),
        )
        assert sent[0]["type"] == "selection_update"
        assert sent[0]["displayName"] == "Ana Silva"
        assert sent[0]["selectedIds"] == ["block-1", "block-2"]

    asyncio.run(_run())


def test_realtime_hub_presence_leave_removes_peer():
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        alive = FakeWebSocket()
        leaving = FakeWebSocket()
        hub._rooms["playlist-1"] = {alive, leaving}  # noqa: SLF001
        hub._sessions[leaving] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-2",
            display_name="Michael Marotto",
            role="editor",
            can_edit=True,
        )
        hub._sessions[alive] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-1",
            display_name="Ana",
            role="editor",
            can_edit=True,
        )
        await hub._handle_message(  # noqa: SLF001
            alive,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-ana"}',
        )
        await hub._handle_message(  # noqa: SLF001
            leaving,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-michael"}',
        )
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            leaving,
            playlist_id="playlist-1",
            message='{"type":"presence_leave","clientId":"editor-michael"}',
        )
        assert sent[-1]["type"] == "presence_update"
        peers = sent[-1]["peers"]
        assert len(peers) == 1
        assert peers[0]["clientId"] == "editor-ana"
        assert peers[0]["displayName"] == "Ana"

    asyncio.run(_run())


def test_realtime_hub_purges_stale_presence_on_ping():
    import asyncio
    import time

    async def _run() -> None:
        hub = PresentationRealtimeHub(presence_stale_ttl_seconds=30)
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        alive = FakeWebSocket()
        stale = FakeWebSocket()
        hub._rooms["playlist-1"] = {alive, stale}  # noqa: SLF001
        hub._sessions[alive] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-1",
            display_name="Ana",
            role="editor",
            can_edit=True,
        )
        hub._sessions[stale] = PresentationRealtimeSession(  # noqa: SLF001
            user_id="user-2",
            display_name="Michael Marotto",
            role="editor",
            can_edit=True,
        )
        await hub._handle_message(  # noqa: SLF001
            alive,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-ana"}',
        )
        await hub._handle_message(  # noqa: SLF001
            stale,
            playlist_id="playlist-1",
            message='{"type":"presence_join","clientId":"editor-michael"}',
        )
        # Simula peer morto: lastSeen antigo sem leave/disconnect limpo.
        hub._client_meta["playlist-1"][stale]["lastSeen"] = time.monotonic() - 120  # noqa: SLF001
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            alive,
            playlist_id="playlist-1",
            message='{"type":"presence_ping","clientId":"editor-ana"}',
        )
        assert sent[-1]["type"] == "presence_update"
        peers = sent[-1]["peers"]
        assert len(peers) == 1
        assert peers[0]["clientId"] == "editor-ana"

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


def test_public_presentation_ws_is_read_only():
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
        with client.websocket_connect("/public/present/tok-presence/ws") as ws:
            assert ws.receive_json()["type"] == "connected"
            ws.send_json(
                {
                    "type": "selection_update",
                    "clientId": "forged-editor",
                    "slideId": "slide-a",
                    "selectedIds": ["block-1"],
                }
            )
            ws.send_text("ping")
            assert ws.receive_json()["type"] == "pong"


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


def test_realtime_hub_broadcasts_playback_cursor_without_presence():
    """Viewers públicos (allow_presence=False) podem publicar cursor de reunião."""
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        websocket = FakeWebSocket()
        peer = FakeWebSocket()
        hub._rooms["playlist-1"] = {websocket, peer}  # noqa: SLF001
        hub._sessions[websocket] = PresentationRealtimeSession(  # noqa: SLF001
            user_id=None,
            display_name="TV",
            role="viewer",
            can_edit=False,
            allow_presence=False,
        )
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message=(
                '{"type":"playback_cursor","clientId":"tv-a","slideId":"slide-2","index":1}'
            ),
        )
        assert len(sent) == 2
        assert all(item["type"] == "playback_cursor" for item in sent)
        assert sent[0]["slideId"] == "slide-2"
        assert sent[0]["clientId"] == "tv-a"
        assert sent[0]["index"] == 1
        assert hub._playback_cursors["playlist-1"]["slideId"] == "slide-2"  # noqa: SLF001

    asyncio.run(_run())


def test_realtime_hub_sends_playback_cursor_snapshot_on_connect():
    import asyncio

    from starlette.websockets import WebSocketDisconnect

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        received: list[dict] = []

        class FakeWebSocket:
            async def accept(self) -> None:
                return None

            async def send_json(self, payload: dict) -> None:
                received.append(payload)

            async def receive_text(self) -> str:
                raise WebSocketDisconnect()

        hub._playback_cursors["playlist-1"] = {  # noqa: SLF001
            "type": "playback_cursor",
            "playlistId": "playlist-1",
            "slideId": "slide-9",
            "clientId": "tv-a",
            "index": 3,
            "updatedAt": 1,
        }
        session = PresentationRealtimeSession(
            user_id=None,
            display_name="TV",
            role="viewer",
            can_edit=False,
            allow_presence=False,
        )
        await hub.connect(FakeWebSocket(), playlist_id="playlist-1", session=session)
        assert received[0]["type"] == "connected"
        assert received[1]["type"] == "playback_cursor"
        assert received[1]["slideId"] == "slide-9"

    asyncio.run(_run())


def test_realtime_hub_broadcasts_meeting_laser_and_ink():
    import asyncio

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        sent: list[dict] = []

        class FakeWebSocket:
            async def send_json(self, payload: dict) -> None:
                sent.append(payload)

        websocket = FakeWebSocket()
        peer = FakeWebSocket()
        hub._rooms["playlist-1"] = {websocket, peer}  # noqa: SLF001
        hub._sessions[websocket] = PresentationRealtimeSession(  # noqa: SLF001
            user_id=None,
            display_name="TV",
            role="viewer",
            can_edit=False,
            allow_presence=False,
        )
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message=(
                '{"type":"meeting_laser","clientId":"tv-a","slideId":"s1",'
                '"x":0.5,"y":0.25,"visible":true}'
            ),
        )
        assert len(sent) == 2
        assert sent[0]["type"] == "meeting_laser"
        assert sent[0]["x"] == 0.5
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message=(
                '{"type":"meeting_ink_stroke","clientId":"tv-a","slideId":"s1",'
                '"strokeId":"st-1","phase":"start","points":[{"x":0.1,"y":0.2}]}'
            ),
        )
        assert sent[0]["type"] == "meeting_ink_stroke"
        assert sent[0]["phase"] == "start"
        sent.clear()
        await hub._handle_message(  # noqa: SLF001
            websocket,
            playlist_id="playlist-1",
            message='{"type":"meeting_ink_clear","clientId":"tv-a","slideId":"s1"}',
        )
        assert sent[0]["type"] == "meeting_ink_clear"

    asyncio.run(_run())


def test_realtime_hub_connect_does_not_snapshot_meeting_ink():
    import asyncio

    from starlette.websockets import WebSocketDisconnect

    async def _run() -> None:
        hub = PresentationRealtimeHub()
        received: list[dict] = []

        class FakeWebSocket:
            async def accept(self) -> None:
                return None

            async def send_json(self, payload: dict) -> None:
                received.append(payload)

            async def receive_text(self) -> str:
                raise WebSocketDisconnect()

        session = PresentationRealtimeSession(
            user_id=None,
            display_name="TV",
            role="viewer",
            can_edit=False,
            allow_presence=False,
        )
        await hub.connect(FakeWebSocket(), playlist_id="playlist-1", session=session)
        assert received[0]["type"] == "connected"
        assert all(item["type"] != "meeting_ink_stroke" for item in received)
        assert all(item["type"] != "meeting_laser" for item in received)

    asyncio.run(_run())
