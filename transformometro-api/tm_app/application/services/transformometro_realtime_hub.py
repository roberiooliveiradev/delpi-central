from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from tm_app.core.serialize import json_safe
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

OnRealtimeMessage = Callable[[WebSocket, str], Awaitable[None]]


OnUserDisconnect = Callable[[str, str, int], Awaitable[None]]


class TransformometroRealtimeHub:
    """Salas WebSocket por entidade (entity_type:entity_id)."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._socket_meta: dict[WebSocket, tuple[str, str | None]] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] | None = None

    def count_user_connections(self, room_key: str, user_id: str) -> int:
        return sum(
            1
            for socket_room, socket_user in self._socket_meta.values()
            if socket_room == room_key and socket_user == user_id
        )

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue = asyncio.Queue()

    async def worker(self) -> None:
        if self._queue is None:
            return
        while True:
            room_key, payload = await self._queue.get()
            try:
                await self.broadcast_now(room_key, payload)
            except Exception:  # noqa: BLE001
                logger.exception("transformometro_realtime_broadcast_failed")

    def schedule_broadcast(self, room_key: str, payload: dict[str, Any]) -> None:
        if not room_key or self._loop is None or self._queue is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (room_key, payload))

    async def connect(
        self,
        websocket: WebSocket,
        *,
        room_key: str,
        user_id: str | None,
        client_id: str | None,
        on_message: OnRealtimeMessage | None = None,
        on_user_disconnect: OnUserDisconnect | None = None,
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(room_key, set()).add(websocket)
            self._socket_meta[websocket] = (room_key, user_id)
        try:
            await websocket.send_json(
                {
                    "type": "connected",
                    "roomKey": room_key,
                    "userId": user_id,
                    "clientId": client_id or "",
                }
            )
            while True:
                message = await websocket.receive_text()
                if on_message is not None:
                    await on_message(websocket, message)
                elif message.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            remaining_for_user = 0
            async with self._lock:
                self._socket_meta.pop(websocket, None)
                room = self._rooms.get(room_key)
                if room:
                    room.discard(websocket)
                    if not room:
                        del self._rooms[room_key]
                if user_id:
                    remaining_for_user = self.count_user_connections(room_key, user_id)
            if on_user_disconnect is not None and user_id:
                try:
                    await on_user_disconnect(room_key, user_id, remaining_for_user)
                except Exception:  # noqa: BLE001 — cleanup não pode derrubar o handler WS
                    logger.exception(
                        "transformometro_realtime_on_user_disconnect_failed room=%s user=%s",
                        room_key,
                        user_id,
                    )

    async def broadcast_now(self, room_key: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._rooms.get(room_key, set()))
        if not targets:
            return
        dead: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_json(json_safe(payload))
            except Exception:  # noqa: BLE001
                dead.append(websocket)
        if not dead:
            return
        async with self._lock:
            room = self._rooms.get(room_key)
            if not room:
                return
            for websocket in dead:
                room.discard(websocket)
                self._socket_meta.pop(websocket, None)
            if not room:
                del self._rooms[room_key]


transformometro_realtime_hub = TransformometroRealtimeHub()
