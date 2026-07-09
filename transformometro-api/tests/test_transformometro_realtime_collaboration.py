import json
from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock

from tm_app.application.services.transformometro_realtime_collaboration import (
    TransformometroRealtimeCollaborationHandler,
)


@pytest.mark.asyncio
async def test_realtime_presence_request_replies_to_client():
    service = MagicMock()
    service.list_presence.return_value = {
        "entity_type": "processo",
        "entity_id": "p1",
        "viewers": [],
        "editors": [],
    }
    websocket = AsyncMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)

    await handler.handle_message(
        websocket,
        raw_message='{"type":"presence.request"}',
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )

    websocket.send_json.assert_awaited()
    payload = websocket.send_json.await_args.args[0]
    assert payload["type"] == "presence.updated"
    assert payload["data"]["entity_id"] == "p1"


@pytest.mark.asyncio
async def test_realtime_presence_request_serializes_datetime_payload():
    service = MagicMock()
    service.list_presence.return_value = {
        "entity_type": "processo",
        "entity_id": "p1",
        "viewers": [
            {
                "user_id": "u1",
                "user_name": "Ana",
                "section_key": "",
                "mode": "viewing",
                "lock_active": False,
                "heartbeat_at": datetime(2026, 7, 9, 18, 0, tzinfo=timezone.utc),
            }
        ],
        "editors": [],
    }
    websocket = AsyncMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)

    await handler.handle_message(
        websocket,
        raw_message='{"type":"presence.request"}',
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )

    payload = websocket.send_json.await_args.args[0]
    json.dumps(payload)
    assert payload["data"]["viewers"][0]["heartbeat_at"] == "2026-07-09T18:00:00+00:00"


@pytest.mark.asyncio
async def test_realtime_presence_leave_clears_user_when_alone(monkeypatch):
    service = MagicMock()
    websocket = AsyncMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)
    broadcast = MagicMock()
    monkeypatch.setattr(handler, "_broadcast_presence", broadcast)
    monkeypatch.setattr(
        "tm_app.application.services.transformometro_realtime_collaboration.transformometro_realtime_hub.count_user_connections",
        lambda _room, _user: 0,
    )

    await handler.handle_message(
        websocket,
        raw_message='{"type":"presence.leave"}',
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )

    service.clear_user_presence.assert_called_once_with(
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
    )
    broadcast.assert_called_once_with("processo", "p1")


@pytest.mark.asyncio
async def test_realtime_presence_leave_skips_when_other_connections(monkeypatch):
    service = MagicMock()
    websocket = AsyncMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)
    broadcast = MagicMock()
    monkeypatch.setattr(handler, "_broadcast_presence", broadcast)
    monkeypatch.setattr(
        "tm_app.application.services.transformometro_realtime_collaboration.transformometro_realtime_hub.count_user_connections",
        lambda _room, _user: 1,
    )

    await handler.handle_message(
        websocket,
        raw_message='{"type":"presence.leave"}',
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )

    service.clear_user_presence.assert_not_called()
    broadcast.assert_not_called()


@pytest.mark.asyncio
async def test_realtime_disconnect_clears_user_when_last_connection(monkeypatch):
    service = MagicMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)
    broadcast = MagicMock()
    monkeypatch.setattr(handler, "_broadcast_presence", broadcast)

    await handler.handle_disconnect(
        entity_type="processo",
        entity_id="p1",
        user_id="u2",
        remaining_connections=0,
    )

    service.clear_user_presence.assert_called_once_with(
        entity_type="processo",
        entity_id="p1",
        user_id="u2",
    )
    broadcast.assert_called_once_with("processo", "p1")


@pytest.mark.asyncio
async def test_realtime_disconnect_skips_when_other_connections():
    service = MagicMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)

    await handler.handle_disconnect(
        entity_type="processo",
        entity_id="p1",
        user_id="u2",
        remaining_connections=1,
    )

    service.clear_user_presence.assert_not_called()


def test_clear_user_presence_http_respects_active_connections(monkeypatch):
    service = MagicMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)
    monkeypatch.setattr(
        "tm_app.application.services.transformometro_realtime_collaboration.transformometro_realtime_hub.count_user_connections",
        lambda _room, _user: 2,
    )

    cleared = handler.clear_user_presence_http(
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
    )

    assert cleared is False
    service.clear_user_presence.assert_not_called()


@pytest.mark.asyncio
async def test_realtime_lock_acquire_returns_result():
    service = MagicMock()
    service.acquire_lock.return_value = {"acquired": True, "presence": {"section_key": "diagrama_macro"}}
    websocket = AsyncMock()
    handler = TransformometroRealtimeCollaborationHandler(service=service)

    await handler.handle_message(
        websocket,
        raw_message='{"type":"lock.acquire","sectionKey":"diagrama_macro"}',
        entity_type="processo",
        entity_id="p1",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )

    payload = websocket.send_json.await_args.args[0]
    assert payload["type"] == "lock.result"
    assert payload["sectionKey"] == "diagrama_macro"
    assert payload["data"]["acquired"] is True
