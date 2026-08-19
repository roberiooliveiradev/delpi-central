from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Awaitable, Callable

from commercial_app.core.serialize import json_safe
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

TEAM_ROOM = "team"
# Cliente envia ping a cada ~25s; sem tráfego além disso → socket zumbi (ex.: unmount falhou).
PRESENCE_IDLE_SECONDS = 75.0

ClientTextHandler = Callable[[WebSocket, str], Awaitable[None]]


def presence_updated_payload(online_user_ids: list[str]) -> dict[str, Any]:
    return {
        "type": "presence.updated",
        "onlineUserIds": list(online_user_ids),
    }


class CommercialRealtimeHub:
    """Salas WebSocket: user:{userId}, team (gestores), interaction (inbox) e room:{uuid} (subscribe).

    Presença: conta sockets por user_id (multi-aba = 1 online). Gestores na
    sala `team` recebem `presence.updated` + snapshot ao entrar.
    """

    def __init__(self, *, idle_seconds: float = PRESENCE_IDLE_SECONDS) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._socket_meta: dict[WebSocket, tuple[tuple[str, ...], str | None]] = {}
        self._user_socket_counts: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] | None = None
        self._idle_seconds = float(idle_seconds)

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

    def online_user_ids(self) -> list[str]:
        return sorted(
            user_id
            for user_id, count in self._user_socket_counts.items()
            if count > 0 and user_id
        )

    def is_user_online(self, user_id: str | None) -> bool:
        uid = str(user_id or "").strip()
        if not uid:
            return False
        return self._user_socket_counts.get(uid, 0) > 0

    def presence_payload(self) -> dict[str, Any]:
        return presence_updated_payload(self.online_user_ids())

    async def connect(
        self,
        websocket: WebSocket,
        *,
        room_keys: list[str],
        user_id: str | None,
        client_id: str | None,
        on_text: ClientTextHandler | None = None,
    ) -> None:
        normalized = [key for key in room_keys if key]
        if not normalized:
            raise ValueError("room_keys required")
        await websocket.accept()
        uid = str(user_id or "").strip() or None
        came_online = False
        async with self._lock:
            for room_key in normalized:
                self._rooms.setdefault(room_key, set()).add(websocket)
            self._socket_meta[websocket] = (tuple(normalized), uid)
            if uid:
                previous = self._user_socket_counts.get(uid, 0)
                self._user_socket_counts[uid] = previous + 1
                came_online = previous == 0
        try:
            await websocket.send_json(
                {
                    "type": "connected",
                    "roomKeys": normalized,
                    "userId": uid,
                    "clientId": client_id or "",
                }
            )
            if TEAM_ROOM in normalized:
                await websocket.send_json(json_safe(self.presence_payload()))
            if came_online:
                await self.broadcast_now(TEAM_ROOM, self.presence_payload())
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=self._idle_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.info(
                        "commercial_realtime_idle_timeout user_id=%s",
                        uid,
                    )
                    with contextlib.suppress(Exception):
                        await websocket.close(code=1000)
                    break
                if message.strip().lower() == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                if on_text is not None:
                    await on_text(websocket, message)
        except WebSocketDisconnect:
            pass
        finally:
            await self._disconnect(websocket, fallback_rooms=normalized)

    async def _disconnect(
        self,
        websocket: WebSocket,
        *,
        fallback_rooms: list[str],
    ) -> None:
        went_offline = False
        async with self._lock:
            meta = self._socket_meta.pop(websocket, None)
            keys = list(meta[0]) if meta else list(fallback_rooms)
            uid = meta[1] if meta else None
            for room_key in keys:
                room = self._rooms.get(room_key)
                if room:
                    room.discard(websocket)
                    if not room:
                        del self._rooms[room_key]
            if uid:
                previous = self._user_socket_counts.get(uid, 0)
                if previous <= 1:
                    self._user_socket_counts.pop(uid, None)
                    went_offline = previous == 1
                else:
                    self._user_socket_counts[uid] = previous - 1
        if went_offline:
            await self.broadcast_now(TEAM_ROOM, self.presence_payload())

    async def join_room(self, websocket: WebSocket, room_key: str) -> bool:
        key = (room_key or "").strip()
        if not key:
            return False
        async with self._lock:
            meta = self._socket_meta.get(websocket)
            if meta is None:
                return False
            keys = list(meta[0])
            if key not in keys:
                keys.append(key)
            self._rooms.setdefault(key, set()).add(websocket)
            self._socket_meta[websocket] = (tuple(keys), meta[1])
        return True

    async def leave_room(self, websocket: WebSocket, room_key: str) -> bool:
        key = (room_key or "").strip()
        if not key:
            return False
        async with self._lock:
            meta = self._socket_meta.get(websocket)
            if meta is None:
                return False
            keys = [item for item in meta[0] if item != key]
            self._socket_meta[websocket] = (tuple(keys), meta[1])
            room = self._rooms.get(key)
            if room:
                room.discard(websocket)
                if not room:
                    del self._rooms[key]
        return True

    def socket_room_keys(self, websocket: WebSocket) -> tuple[str, ...]:
        meta = self._socket_meta.get(websocket)
        if meta is None:
            return ()
        return meta[0]

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
        for websocket in dead:
            await self._disconnect(websocket, fallback_rooms=[])


commercial_realtime_hub = CommercialRealtimeHub()
