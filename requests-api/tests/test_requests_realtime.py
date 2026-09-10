from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock

from requests_app.application.services.requests_realtime_hub import RequestsRealtimeHub
from requests_app.application.services.requests_realtime_notify import (
    WORK_QUEUE_ROOM,
    notify_request_changed,
    notify_request_created,
    notify_request_timeline,
    request_room,
    user_room,
)
from requests_app.application.services.requests_realtime_protocol import (
    handle_realtime_client_message,
    parse_request_subscription,
)


def test_user_and_request_room_keys():
    assert user_room("abc") == "user:abc"
    assert request_room("11111111-1111-1111-1111-111111111111") == (
        "request:11111111-1111-1111-1111-111111111111"
    )
    assert WORK_QUEUE_ROOM == "work-queue"


def test_parse_request_subscription_accepts_request_id():
    assert parse_request_subscription(
        '{"type":"subscribe","requestId":"11111111-1111-1111-1111-111111111111"}'
    ) == ("subscribe", "11111111-1111-1111-1111-111111111111")


def test_hub_broadcasts_to_room():
    async def run() -> None:
        hub = RequestsRealtimeHub()
        loop = asyncio.get_running_loop()
        hub.bind_loop(loop)
        worker = asyncio.create_task(hub.worker())

        socket = AsyncMock()
        socket.send_json = AsyncMock()
        hub._rooms["user:owner"] = {socket}  # noqa: SLF001

        await hub.broadcast_now(
            "user:owner", {"type": "request.created", "requestId": "1"}
        )
        socket.send_json.assert_awaited_once()
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker

    asyncio.run(run())


def test_protocol_subscribe_fail_closed():
    async def run() -> None:
        hub = RequestsRealtimeHub()
        socket = AsyncMock()
        socket.send_json = AsyncMock()
        hub._socket_meta[socket] = (("user:u1",), "u1")  # noqa: SLF001

        ack = await handle_realtime_client_message(
            hub=hub,
            websocket=socket,
            user_id="u1",
            raw='{"type":"subscribe","requestId":"11111111-1111-1111-1111-111111111111"}',
            can_join_request=lambda _uid, _rid: False,
        )
        assert ack is not None
        assert ack["type"] == "error"
        assert ack["code"] == "accessDenied"

    asyncio.run(run())


def test_protocol_subscribe_joins_request_room():
    async def run() -> None:
        hub = RequestsRealtimeHub()
        socket = AsyncMock()
        socket.send_json = AsyncMock()
        rid = "11111111-1111-1111-1111-111111111111"
        hub._socket_meta[socket] = (("user:u1",), "u1")  # noqa: SLF001

        ack = await handle_realtime_client_message(
            hub=hub,
            websocket=socket,
            user_id="u1",
            raw=f'{{"type":"subscribe","requestId":"{rid}"}}',
            can_join_request=lambda _uid, _rid: True,
        )
        assert ack is not None
        assert ack["type"] == "subscribed"
        assert ack["roomKey"] == request_room(rid)
        assert request_room(rid) in hub.socket_room_keys(socket)

    asyncio.run(run())


def test_notify_request_created_schedules_work_queue_and_owner(monkeypatch):
    scheduled: list[tuple[list[str], dict]] = []

    class HubStub:
        def schedule_broadcast_rooms(self, room_keys, payload):
            scheduled.append((list(room_keys), payload))

    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.requests_realtime_hub",
        HubStub(),
    )
    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.settings.REQUESTS_REALTIME_ENABLED",
        True,
    )

    notify_request_created(
        request_id="r1",
        request_number="REQ-1",
        status="submitted",
        owner_user_id="owner-1",
        actor_user_id="owner-1",
    )
    rooms = {r for keys, _ in scheduled for r in keys}
    assert WORK_QUEUE_ROOM in rooms
    assert "user:owner-1" in rooms
    assert scheduled[0][1]["type"] == "request.created"


def test_notify_request_changed_and_timeline(monkeypatch):
    scheduled: list[tuple[list[str], dict]] = []

    class HubStub:
        def schedule_broadcast_rooms(self, room_keys, payload):
            scheduled.append((list(room_keys), payload))

    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.requests_realtime_hub",
        HubStub(),
    )
    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.settings.REQUESTS_REALTIME_ENABLED",
        True,
    )

    notify_request_changed(
        reason="transition.start",
        request_id="11111111-1111-1111-1111-111111111111",
        status="in_progress",
        owner_user_id="owner-1",
        actor_user_id="proc-1",
        notification={"title": "Atualizada", "message": "Iniciada", "variant": "info"},
    )
    changed_rooms = {r for keys, p in scheduled if p["type"] == "request.changed" for r in keys}
    assert request_room("11111111-1111-1111-1111-111111111111") in changed_rooms
    assert WORK_QUEUE_ROOM in changed_rooms
    assert "user:owner-1" in changed_rooms

    scheduled.clear()
    notify_request_timeline(
        reason="comment.created",
        request_id="11111111-1111-1111-1111-111111111111",
        owner_user_id="owner-1",
        assignee_user_id="proc-1",
    )
    timeline_rooms = {r for keys, _ in scheduled for r in keys}
    assert timeline_rooms == {
        request_room("11111111-1111-1111-1111-111111111111"),
        "user:owner-1",
        "user:proc-1",
    }

def test_notify_disabled_is_noop(monkeypatch):
    called = []

    class HubStub:
        def schedule_broadcast(self, room_key, payload):
            called.append((room_key, payload))

    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.requests_realtime_hub",
        HubStub(),
    )
    monkeypatch.setattr(
        "requests_app.application.services.requests_realtime_notify.settings.REQUESTS_REALTIME_ENABLED",
        False,
    )
    notify_request_created(request_id="r1", owner_user_id="o1")
    assert called == []
