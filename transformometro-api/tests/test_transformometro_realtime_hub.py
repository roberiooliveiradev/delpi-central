import pytest
from unittest.mock import AsyncMock, MagicMock

from tm_app.application.services.transformometro_realtime_hub import TransformometroRealtimeHub


@pytest.mark.asyncio
async def test_hub_counts_user_connections_per_room():
    hub = TransformometroRealtimeHub()
    room = "processo:p1"
    socket_a = MagicMock()
    socket_b = MagicMock()
    socket_c = MagicMock()

    hub._rooms[room] = {socket_a, socket_b, socket_c}
    hub._socket_meta[socket_a] = (room, "u1")
    hub._socket_meta[socket_b] = (room, "u1")
    hub._socket_meta[socket_c] = (room, "u2")

    assert hub.count_user_connections(room, "u1") == 2
    assert hub.count_user_connections(room, "u2") == 1
    assert hub.count_user_connections(room, "u3") == 0


@pytest.mark.asyncio
async def test_hub_disconnect_callback_only_when_last_connection():
    hub = TransformometroRealtimeHub()
    room = "processo:p1"
    socket_a = AsyncMock()
    socket_b = AsyncMock()
    disconnect_calls: list[int] = []

    async def on_user_disconnect(_room_key: str, _user_id: str, remaining: int) -> None:
        disconnect_calls.append(remaining)

    hub._rooms[room] = {socket_a, socket_b}
    hub._socket_meta[socket_a] = (room, "u1")
    hub._socket_meta[socket_b] = (room, "u1")

    async with hub._lock:
        hub._socket_meta.pop(socket_a, None)
        hub._rooms[room].discard(socket_a)
        remaining = hub.count_user_connections(room, "u1")
    await on_user_disconnect(room, "u1", remaining)

    assert disconnect_calls == [1]

    async with hub._lock:
        hub._socket_meta.pop(socket_b, None)
        hub._rooms[room].discard(socket_b)
        remaining = hub.count_user_connections(room, "u1")
    await on_user_disconnect(room, "u1", remaining)

    assert disconnect_calls == [1, 0]
