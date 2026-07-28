from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from tv_app.application.services.presentation_realtime_models import (
    PresentationRealtimeSession,
)

logger = logging.getLogger(__name__)

# Sem ping/leave por este intervalo → peer some de «Também editando».
# Cliente envia presence_ping a cada ~30s; 3 misses cobrem aba morta / half-open.
PRESENCE_STALE_TTL_SECONDS = 90.0


class PresentationRealtimeHub:
    """Salas WebSocket por programação (playlist_id)."""

    def __init__(
        self,
        *,
        presence_stale_ttl_seconds: float = PRESENCE_STALE_TTL_SECONDS,
    ) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._client_meta: dict[str, dict[WebSocket, dict[str, Any]]] = {}
        self._sessions: dict[WebSocket, PresentationRealtimeSession] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] | None = None
        self._presence_stale_ttl_seconds = max(15.0, float(presence_stale_ttl_seconds))

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

    async def connect(
        self,
        websocket: WebSocket,
        *,
        playlist_id: str,
        session: PresentationRealtimeSession,
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(playlist_id, set()).add(websocket)
            self._sessions[websocket] = session
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
            session = self._sessions.get(websocket)
            if not session or not session.allow_presence or not client_id:
                return
            async with self._lock:
                self._client_meta.setdefault(playlist_id, {})[websocket] = {
                    "clientId": client_id,
                    "userId": session.user_id,
                    "displayName": session.display_name,
                    "role": session.role,
                    "canEdit": session.can_edit,
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
            session = self._sessions.get(websocket)
            presence_changed = False
            async with self._lock:
                now = time.monotonic()
                room_meta = self._client_meta.setdefault(playlist_id, {})
                current = room_meta.get(websocket)
                if current and current["clientId"] == client_id:
                    current["lastSeen"] = now
                elif session and session.allow_presence:
                    # Rehidrata presença se o TTL limpou o meta enquanto o socket segue vivo.
                    room_meta[websocket] = {
                        "clientId": client_id,
                        "userId": session.user_id,
                        "displayName": session.display_name,
                        "role": session.role,
                        "canEdit": session.can_edit,
                        "lastSeen": now,
                    }
                    presence_changed = True
                presence_changed = (
                    self._purge_stale_presence_locked(playlist_id, now=now) or presence_changed
                )
            if presence_changed:
                await self._broadcast_presence(playlist_id)
            return

        if message_type == "slide_draft":
            slide_id = self._clean_text(payload.get("slideId"))
            native_config = payload.get("nativeConfig")
            current = self._client_meta.get(playlist_id, {}).get(websocket)
            if (
                not current
                or not current.get("canEdit")
                or current.get("clientId") != client_id
                or not slide_id
                or not isinstance(native_config, dict)
            ):
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
            return

        if message_type == "selection_update":
            slide_id = self._clean_text(payload.get("slideId"))
            raw_selected_ids = payload.get("selectedIds")
            current = self._client_meta.get(playlist_id, {}).get(websocket)
            if (
                not current
                or not current.get("canEdit")
                or current.get("clientId") != client_id
                or not slide_id
                or not isinstance(raw_selected_ids, list)
            ):
                return
            selected_ids: list[str] = []
            for raw_id in raw_selected_ids[:100]:
                block_id = self._clean_text(raw_id)
                if block_id and block_id not in selected_ids:
                    selected_ids.append(block_id)
            await self.broadcast_now(
                playlist_id,
                {
                    "type": "selection_update",
                    "playlistId": playlist_id,
                    "slideId": slide_id,
                    "clientId": client_id,
                    "displayName": current["displayName"],
                    "selectedIds": selected_ids,
                    "updatedAt": int(time.time() * 1000),
                },
            )

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        return cleaned or None

    def _purge_stale_presence_locked(
        self,
        playlist_id: str,
        *,
        now: float | None = None,
    ) -> bool:
        """Remove metas sem ping recente. Caller deve segurar ``_lock``."""
        room_meta = self._client_meta.get(playlist_id)
        if not room_meta:
            return False
        cutoff = (now if now is not None else time.monotonic()) - self._presence_stale_ttl_seconds
        stale = [
            (websocket, meta)
            for websocket, meta in list(room_meta.items())
            if float(meta.get("lastSeen") or 0) < cutoff
        ]
        if not stale:
            return False
        for websocket, meta in stale:
            room_meta.pop(websocket, None)
            logger.info(
                "presentation_presence_stale_purged playlist_id=%s client_id=%s",
                playlist_id,
                meta.get("clientId"),
            )
        if not room_meta:
            del self._client_meta[playlist_id]
        return True

    async def _presence_payload(self, playlist_id: str) -> dict[str, Any]:
        async with self._lock:
            self._purge_stale_presence_locked(playlist_id)
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
            self._sessions.pop(websocket, None)
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
