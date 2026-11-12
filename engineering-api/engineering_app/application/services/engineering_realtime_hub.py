"""Hub WebSocket transversal da Engineering API — ENG-REALTIME-01.

Adaptado do padrão ``requests-api`` (hub process-local): rooms
``user:{sub}`` (identidade), ``queue:{domain}`` (escopo de fila) e
``res:{domain}:{resourceId}`` (assinatura por objeto).

Diferença material: cada assinatura guarda um ``authorizer`` fornecido
pelo adapter do domínio. Antes de **cada entrega** o hub reexecuta o
authorizer — revogação de acesso ao objeto (ex.: reatribuição,
solicitante diverso) bloqueia entregas futuras na conexão ativa sem
depender de reconexão.

Process-local: exige exatamente 1 worker uvicorn por instância
(topologia comprovada em F0 — Dockerfile sem ``--workers`` e compose
sem réplicas).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Awaitable, Callable

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

# Cliente envia ping a cada ~25s; sem tráfego além disso → socket zumbi.
PRESENCE_IDLE_SECONDS = 75.0

RoomAuthorizer = Callable[[], bool]
ClientTextHandler = Callable[[WebSocket, str], Awaitable[None]]


class EngineeringRealtimeHub:
    """Salas WebSocket neutras — sem conhecimento de domínio PRC."""

    def __init__(self, *, idle_seconds: float = PRESENCE_IDLE_SECONDS) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        # socket → (rooms, user_id); socket+room → authorizer
        self._socket_meta: dict[WebSocket, tuple[set[str], str | None]] = {}
        self._room_authorizers: dict[WebSocket, dict[str, RoomAuthorizer]] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[tuple[str, ...], dict[str, Any]]] | None = None
        self._worker_task: asyncio.Task | None = None
        self._idle_seconds = float(idle_seconds)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue = asyncio.Queue()

    async def worker(self) -> None:
        if self._queue is None:
            return
        while True:
            room_keys, payload = await self._queue.get()
            try:
                await self.broadcast_now_rooms(room_keys, payload)
            except Exception:  # noqa: BLE001
                logger.exception("engineering_realtime_broadcast_failed")

    def schedule_broadcast_rooms(
        self, room_keys: list[str], payload: dict[str, Any]
    ) -> None:
        if self._loop is None or self._queue is None:
            return
        cleaned: list[str] = []
        seen: set[str] = set()
        for key in room_keys:
            item = (key or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            cleaned.append(item)
        if not cleaned:
            return
        try:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait, (tuple(cleaned), payload)
            )
        except RuntimeError:
            # Loop encerrado (shutdown/teste) — entrega best-effort.
            logger.warning("engineering_realtime_loop_closed")

    async def connect(
        self,
        websocket: WebSocket,
        *,
        room_keys: list[str],
        user_id: str | None,
        client_id: str | None,
        on_text: ClientTextHandler | None = None,
        close_after_seconds: float | None = None,
    ) -> None:
        normalized = {key for key in room_keys if key}
        if not normalized:
            raise ValueError("room_keys required")
        # Bind lazy: cobre contextos sem lifespan (testes) e rebind se
        # o loop guardado for de outro contexto (worker era dele).
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            self.bind_loop(loop)
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self.worker())
        await websocket.accept()
        uid = str(user_id or "").strip() or None
        async with self._lock:
            for room_key in normalized:
                self._rooms.setdefault(room_key, set()).add(websocket)
            self._socket_meta[websocket] = (set(normalized), uid)
        expiry_task: asyncio.Task | None = None
        if close_after_seconds is not None and close_after_seconds > 0:
            expiry_task = asyncio.create_task(
                self._close_at(websocket, close_after_seconds)
            )
        try:
            await websocket.send_json(
                {
                    "type": "connected",
                    "roomKeys": sorted(normalized),
                    "userId": uid,
                    "clientId": client_id or "",
                }
            )
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=self._idle_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.info("engineering_realtime_idle_timeout user_id=%s", uid)
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
            if expiry_task is not None:
                expiry_task.cancel()
            await self._disconnect(websocket)

    async def _close_at(self, websocket: WebSocket, seconds: float) -> None:
        """Encerra o socket na expiração do JWT — revogação limitada à
        vida útil do token (o refresh passa por novo handshake/RBAC)."""
        try:
            await asyncio.sleep(max(0.0, seconds))
            with contextlib.suppress(Exception):
                await websocket.close(code=1000)
        except asyncio.CancelledError:
            return

    async def _disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            meta = self._socket_meta.pop(websocket, None)
            self._room_authorizers.pop(websocket, None)
            keys = meta[0] if meta else set()
            for room_key in keys:
                room = self._rooms.get(room_key)
                if room:
                    room.discard(websocket)
                    if not room:
                        del self._rooms[room_key]

    async def join_room(
        self,
        websocket: WebSocket,
        room_key: str,
        *,
        authorizer: RoomAuthorizer | None = None,
    ) -> bool:
        key = (room_key or "").strip()
        if not key:
            return False
        async with self._lock:
            meta = self._socket_meta.get(websocket)
            if meta is None:
                return False
            meta[0].add(key)
            self._rooms.setdefault(key, set()).add(websocket)
            if authorizer is not None:
                self._room_authorizers.setdefault(websocket, {})[key] = (
                    authorizer
                )
        return True

    async def leave_room(self, websocket: WebSocket, room_key: str) -> bool:
        key = (room_key or "").strip()
        if not key:
            return False
        async with self._lock:
            meta = self._socket_meta.get(websocket)
            if meta is None:
                return False
            meta[0].discard(key)
            self._room_authorizers.get(websocket, {}).pop(key, None)
            room = self._rooms.get(key)
            if room:
                room.discard(websocket)
                if not room:
                    del self._rooms[key]
        return True

    async def broadcast_now_rooms(
        self, room_keys: tuple[str, ...] | list[str], payload: dict[str, Any]
    ) -> None:
        """Send once por socket; reexecuta authorizer por sala antes de
        entregar (revogação por objeto em conexão ativa)."""
        async with self._lock:
            targets: dict[WebSocket, list[str]] = {}
            for room_key in room_keys:
                key = (room_key or "").strip()
                if not key:
                    continue
                for websocket in self._rooms.get(key, set()):
                    targets.setdefault(websocket, []).append(key)
        if not targets:
            return
        dead: list[WebSocket] = []
        denied: list[tuple[WebSocket, str]] = []
        for websocket, keys in targets.items():
            allowed = True
            authorizers = self._room_authorizers.get(websocket, {})
            for key in keys:
                authorizer = authorizers.get(key)
                if authorizer is None:
                    continue
                try:
                    if not authorizer():
                        allowed = False
                        denied.append((websocket, key))
                        break
                except Exception:  # noqa: BLE001
                    # fail-closed: erro de autorização bloqueia a entrega
                    allowed = False
                    denied.append((websocket, key))
                    logger.warning(
                        "engineering_realtime_authorizer_failed room=%s",
                        key,
                        exc_info=True,
                    )
                    break
            if not allowed:
                continue
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(websocket)
        for websocket, key in denied:
            await self.leave_room(websocket, key)
        for websocket in dead:
            await self._disconnect(websocket)


engineering_realtime_hub = EngineeringRealtimeHub()
