from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class MachineLoadRealtimeHub:
    """Salas WebSocket por filial — avisa o cockpit do operador quando o PCP altera a fila.

    O payload é só um aviso (`type` + `reason`); o cliente refaz a leitura HTTP pública,
    mantendo uma única fonte de verdade para o conteúdo da fila.
    """

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
            room, payload = await self._queue.get()
            try:
                await self.broadcast_now(room, payload)
            except Exception:  # noqa: BLE001
                logger.exception("machine_load_realtime_broadcast_failed")

    def schedule_broadcast(self, room: str, payload: dict[str, Any]) -> None:
        """Enfileira um broadcast a partir de código síncrono (rotas HTTP)."""
        if not room or self._loop is None or self._queue is None:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (room, payload))

    async def connect(self, websocket: WebSocket, *, room: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(room, set()).add(websocket)
        try:
            await websocket.send_json({"type": "connected", "branch": room})
            while True:
                message = await websocket.receive_text()
                if message.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            pass
        except Exception:  # noqa: BLE001
            logger.debug("machine_load_realtime_socket_closed", exc_info=True)
        finally:
            await self._remove_connection(websocket, room=room)

    async def broadcast_now(self, room: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._rooms.get(room, set()))
        dead: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(websocket)
        for websocket in dead:
            await self._remove_connection(websocket, room=room)

    def connection_count(self, room: str) -> int:
        return len(self._rooms.get(room, set()))

    async def _remove_connection(self, websocket: WebSocket, *, room: str) -> None:
        async with self._lock:
            connections = self._rooms.get(room)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                del self._rooms[room]


machine_load_realtime_hub = MachineLoadRealtimeHub()
