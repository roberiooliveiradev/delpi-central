from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class PresentationRealtimeHub:
    """Salas WebSocket por programação (playlist_id)."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
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
            playlist_id, payload = await self._queue.get()
            try:
                await self.broadcast_now(playlist_id, payload)
            except Exception:  # noqa: BLE001
                logger.exception("presentation_realtime_broadcast_failed")

    def schedule_broadcast(self, playlist_id: str, payload: dict[str, Any]) -> None:
        if not playlist_id or self._loop is None or self._queue is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (playlist_id, payload))

    async def connect(self, websocket: WebSocket, *, playlist_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(playlist_id, set()).add(websocket)
        try:
            await websocket.send_json({"type": "connected", "playlistId": playlist_id})
            while True:
                message = await websocket.receive_text()
                if message.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        finally:
            async with self._lock:
                room = self._rooms.get(playlist_id)
                if not room:
                    return
                room.discard(websocket)
                if not room:
                    del self._rooms[playlist_id]

    async def broadcast_now(self, playlist_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._rooms.get(playlist_id, set()))
        if not targets:
            return
        dead: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(websocket)
        if not dead:
            return
        async with self._lock:
            room = self._rooms.get(playlist_id)
            if not room:
                return
            for websocket in dead:
                room.discard(websocket)
            if not room:
                del self._rooms[playlist_id]


presentation_realtime_hub = PresentationRealtimeHub()
