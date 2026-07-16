from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class PresentationRealtimeHub:
    """Salas WebSocket por programação (playlist_id)."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._client_meta: dict[str, dict[WebSocket, dict[str, Any]]] = {}
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
                    continue
                await self._handle_message(websocket, playlist_id=playlist_id, message=message)
        except WebSocketDisconnect:
            pass
        finally:
            presence_changed = await self._remove_connection(websocket, playlist_id=playlist_id)
            if presence_changed:
                await self._broadcast_presence(playlist_id)

    async def _handle_message(
        self,
        websocket: WebSocket,
        *,
        playlist_id: str,
        message: str,
    ) -> None:
        try:
            payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(payload, dict):
            return

        message_type = payload.get("type")
        client_id = self._clean_text(payload.get("clientId"))
        if message_type == "presence_join":
            display_name = self._clean_text(payload.get("displayName"))
            role = payload.get("role")
            if not client_id or not display_name or role not in {"editor", "viewer"}:
                return
            async with self._lock:
                self._client_meta.setdefault(playlist_id, {})[websocket] = {
                    "clientId": client_id,
                    "displayName": display_name,
                    "role": role,
                    "lastSeen": time.monotonic(),
                }
            await self._broadcast_presence(playlist_id)
            return

        if message_type == "presence_leave" and client_id:
            removed = False
            async with self._lock:
                room_meta = self._client_meta.get(playlist_id)
                current = room_meta.get(websocket) if room_meta else None
                if current and current["clientId"] == client_id:
                    del room_meta[websocket]
                    removed = True
                    if not room_meta:
                        del self._client_meta[playlist_id]
            if removed:
                await self._broadcast_presence(playlist_id)
            return

        if message_type == "presence_ping" and client_id:
            async with self._lock:
                current = self._client_meta.get(playlist_id, {}).get(websocket)
                if current and current["clientId"] == client_id:
                    current["lastSeen"] = time.monotonic()
            return

        if message_type == "slide_draft":
            slide_id = self._clean_text(payload.get("slideId"))
            native_config = payload.get("nativeConfig")
            if not client_id or not slide_id or not isinstance(native_config, dict):
                return
            await self.broadcast_now(
                playlist_id,
                {
                    "type": "slide_draft",
                    "playlistId": playlist_id,
                    "slideId": slide_id,
                    "clientId": client_id,
                    "nativeConfig": native_config,
                },
            )

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        return cleaned or None

    async def _presence_payload(self, playlist_id: str) -> dict[str, Any]:
        async with self._lock:
            peers_by_id: dict[str, dict[str, str]] = {}
            for meta in self._client_meta.get(playlist_id, {}).values():
                peers_by_id[meta["clientId"]] = {
                    "clientId": meta["clientId"],
                    "displayName": meta["displayName"],
                    "role": meta["role"],
                }
        return {
            "type": "presence_update",
            "playlistId": playlist_id,
            "peers": list(peers_by_id.values()),
        }

    async def _broadcast_presence(self, playlist_id: str) -> None:
        await self.broadcast_now(playlist_id, await self._presence_payload(playlist_id))

    async def _remove_connection(self, websocket: WebSocket, *, playlist_id: str) -> bool:
        async with self._lock:
            room = self._rooms.get(playlist_id)
            if room:
                room.discard(websocket)
                if not room:
                    del self._rooms[playlist_id]
            room_meta = self._client_meta.get(playlist_id)
            presence_changed = bool(room_meta and room_meta.pop(websocket, None))
            if room_meta is not None and not room_meta:
                del self._client_meta[playlist_id]
            return presence_changed

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
        presence_changed = False
        for websocket in dead:
            presence_changed = (
                await self._remove_connection(websocket, playlist_id=playlist_id)
                or presence_changed
            )
        if presence_changed:
            await self._broadcast_presence(playlist_id)


presentation_realtime_hub = PresentationRealtimeHub()
