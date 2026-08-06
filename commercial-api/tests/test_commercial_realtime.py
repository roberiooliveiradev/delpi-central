from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

from commercial_app.application.services.commercial_realtime_hub import CommercialRealtimeHub
from commercial_app.application.services.commercial_realtime_notify import (
    TEAM_ROOM,
    notify_worklist_changed,
    user_room,
)


def test_hub_broadcasts_to_room():
    async def run() -> None:
        hub = CommercialRealtimeHub()
        loop = asyncio.get_running_loop()
        hub.bind_loop(loop)
        worker = asyncio.create_task(hub.worker())

        socket = AsyncMock()
        socket.send_json = AsyncMock()

        hub._rooms["user:seller-a"] = {socket}  # noqa: SLF001 — teste de hub

        await hub.broadcast_now("user:seller-a", {"type": "worklist.changed", "taskId": "1"})

        socket.send_json.assert_awaited_once()
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker

    asyncio.run(run())


def test_notify_worklist_changed_schedules_user_and_team(monkeypatch):
    hub = MagicMock()
    scheduled: list[tuple[str, dict]] = []

    def capture(room: str, payload: dict) -> None:
        scheduled.append((room, payload))

    hub.schedule_broadcast = capture
    monkeypatch.setattr(
        "commercial_app.application.services.commercial_realtime_notify.commercial_realtime_hub",
        hub,
    )

    notify_worklist_changed(
        reason="task.created",
        task_id="abc",
        assignee_user_ids=["seller-a"],
        actor_client_id="client-1",
    )

    rooms = {room for room, _ in scheduled}
    assert user_room("seller-a") in rooms
    assert TEAM_ROOM in rooms
    assert scheduled[0][1]["type"] == "worklist.changed"
    assert scheduled[0][1]["reason"] == "task.created"
    assert scheduled[0][1]["actorClientId"] == "client-1"


def test_user_room_key():
    assert user_room("seller-a") == "user:seller-a"
