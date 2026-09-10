from __future__ import annotations

import asyncio
from typing import Any

from requests_app.application.services.requests_realtime_hub import RequestsRealtimeHub


class _FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[Any] = []

    async def send_json(self, payload: Any) -> None:
        self.sent.append(payload)


def test_broadcast_rooms_dedupes_same_socket():
    hub = RequestsRealtimeHub()
    socket = _FakeWebSocket()

    async def _run() -> None:
        async with hub._lock:
            hub._rooms["request:r1"] = {socket}  # type: ignore[arg-type]
            hub._rooms["user:u1"] = {socket}  # type: ignore[arg-type]
            hub._rooms["work-queue"] = {socket}  # type: ignore[arg-type]
        await hub.broadcast_now_rooms(
            ["request:r1", "user:u1", "work-queue"],
            {"type": "request.changed", "requestId": "r1"},
        )

    asyncio.run(_run())
    assert len(socket.sent) == 1
    assert socket.sent[0]["type"] == "request.changed"
