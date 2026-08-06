from __future__ import annotations

import asyncio
import logging
from typing import Any

from commercial_app.core.serialize import json_safe
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class CommercialRealtimeHub:
    """Salas WebSocket: user:{userId} e team (gestores)."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._socket_meta: dict[WebSocket, tuple[tuple[str, ...], str | None]] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] | None = None

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
                logger.exception("commercial_realtime_broadcast_failed")

    def schedule_broadcast(self, room_key: str, payload: dict[str, Any]) -> None:
        if not room_key or self._loop is None or self._queue is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (room_key, payload))

    async def connect(
        self,
        websocket: WebSocket,
        *,
        room_keys: list[str],
        user_id: str | None,
        client_id: str | None,
    ) -> None:
        normalized = [key for key in room_keys if key]
        if not normalized:
            raise ValueError("room_keys required")
        await websocket.accept()
        async with self._lock:
            for room_key in normalized:
                self._rooms.setdefault(room_key, set()).add(websocket)
            self._socket_meta[websocket] = (tuple(normalized), user_id)
        try:
            await websocket.send_json(
                {
                    "type": "connected",
                    "roomKeys": normalized,
                    "userId": user_id,
                    "clientId": client_id or "",
                }
            )
            while True:
                message = await websocket.receive_text()
                if message.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            async with self._lock:
                meta = self._socket_meta.pop(websocket, None)
                keys = meta[0] if meta else normalized
                for room_key in keys:
                    room = self._rooms.get(room_key)
                    if room:
                        room.discard(websocket)
                        if not room:
                            del self._rooms[room_key]

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
            for websocket in dead:
                meta = self._socket_meta.pop(websocket, None)
                keys = meta[0] if meta else ()
                for key in keys:
                    room = self._rooms.get(key)
                    if room:
                        room.discard(websocket)
                        if not room:
                            del self._rooms[key]


commercial_realtime_hub = CommercialRealtimeHub()
