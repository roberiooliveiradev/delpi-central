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
