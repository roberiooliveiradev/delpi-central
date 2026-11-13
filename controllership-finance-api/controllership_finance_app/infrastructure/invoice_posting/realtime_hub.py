"""Hub WebSocket em memória do LNF. Um processo. Sem dados de negócio."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable
from uuid import uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketDisconnected

from controllership_finance_app.application.invoice_posting.change_notifier import (
    ACTOR_ORIGINS,
    QUEUE_RECONCILED,
    REQUEST_CHANGED,
    REQUEST_REASONS,
    UNMAPPED_CHANGED,
)

logger = logging.getLogger(__name__)

SEND_TIMEOUT_SECONDS = 2.0
IDLE_SECONDS = 75.0
UNMAPPED_ROOM = "lnf:unmapped-products"

ClientTextHandler = Callable[[WebSocket, str], Awaitable[None]]


def branch_room(branch: str) -> str:
    return f"lnf:branch:{str(branch).strip()}"


def request_room(request_id: str) -> str:
    return f"lnf:request:{str(request_id).strip()}"


def _envelope(event_type: str, *, branch: str | None, extra: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": event_type,
        "eventId": str(uuid4()),
        "occurredAt": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
    }
    payload.update(extra)
    return payload


class InMemoryInvoicePostingRealtimeHub:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._socket_rooms: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[tuple[tuple[str, ...], dict[str, Any]]] | None = None
        self._worker_task: asyncio.Task | None = None
        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue = asyncio.Queue()

    def request_changed(
        self,
        *,
        branch: str,
        request_id: str,
        reason: str,
        actor_origin: str,
    ) -> None:
        if reason not in REQUEST_REASONS or actor_origin not in ACTOR_ORIGINS:
            return
        clean_branch = str(branch or "").strip()
        clean_id = str(request_id or "").strip()
        if not clean_branch or not clean_id:
            return
        self.schedule_broadcast(
            [branch_room(clean_branch), request_room(clean_id)],
            _envelope(
                REQUEST_CHANGED,
                branch=clean_branch,
                extra={
                    "requestId": clean_id,
                    "reason": reason,
                    "actorOrigin": actor_origin,
                },
            ),
        )

    def queue_reconciled(self, *, branch: str, updated_count: int) -> None:
        count = int(updated_count)
        clean_branch = str(branch or "").strip()
        if count <= 0 or not clean_branch:
            return
        self.schedule_broadcast(
            [branch_room(clean_branch)],
            _envelope(
                QUEUE_RECONCILED,
                branch=clean_branch,
                extra={"updatedCount": count},
            ),
        )

    def unmapped_products_changed(self) -> None:
        self.schedule_broadcast(
            [UNMAPPED_ROOM],
            _envelope(UNMAPPED_CHANGED, branch=None, extra={}),
        )

    def schedule_broadcast(self, room_keys: list[str], payload: dict[str, Any]) -> None:
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
            logger.warning("lnf_realtime_loop_closed")

    async def worker(self) -> None:
        if self._queue is None:
            return
        while True:
            room_keys, payload = await self._queue.get()
            try:
                await self.broadcast_now(room_keys, payload)
            except Exception:  # noqa: BLE001
                logger.warning("lnf_realtime_broadcast_failed")

    async def connect(
        self,
        websocket: WebSocket,
        *,
        on_text: ClientTextHandler | None = None,
        close_after_seconds: float | None = None,
    ) -> None:
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            self.bind_loop(loop)
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self.worker())
        await websocket.accept()
        async with self._lock:
            self._socket_rooms[websocket] = set()
        expiry_task: asyncio.Task | None = None
        if close_after_seconds is not None:
            expiry_task = asyncio.create_task(
                self._close_at(websocket, close_after_seconds)
            )
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=IDLE_SECONDS,
                    )
                except (asyncio.TimeoutError, WebSocketDisconnect, WebSocketDisconnected):
                    with contextlib.suppress(Exception):
                        await websocket.close(code=1000)
                    break
                if message.strip().lower() == "ping":
                    await self._send(websocket, {"type": "pong"})
                    continue
                if on_text is not None:
                    await on_text(websocket, message)
        except WebSocketDisconnect:
            pass
        finally:
            if expiry_task is not None:
                expiry_task.cancel()
            await self.disconnect(websocket)

    async def _close_at(self, websocket: WebSocket, seconds: float) -> None:
        try:
            await self._sleep(max(0.0, seconds))
            with contextlib.suppress(Exception):
                await websocket.close(code=1000)
        except asyncio.CancelledError:
            return

    async def join(self, websocket: WebSocket, room: str) -> bool:
        key = (room or "").strip()
        if not key:
            return False
        async with self._lock:
            rooms = self._socket_rooms.get(websocket)
            if rooms is None:
                return False
            rooms.add(key)
            self._rooms.setdefault(key, set()).add(websocket)
        return True

    async def leave(self, websocket: WebSocket, room: str) -> bool:
        key = (room or "").strip()
        async with self._lock:
            rooms = self._socket_rooms.get(websocket)
            if rooms is None:
                return False
            rooms.discard(key)
            bucket = self._rooms.get(key)
            if bucket is not None:
                bucket.discard(websocket)
                if not bucket:
                    del self._rooms[key]
        return True

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            rooms = self._socket_rooms.pop(websocket, set())
            for key in rooms:
                bucket = self._rooms.get(key)
                if bucket is not None:
                    bucket.discard(websocket)
                    if not bucket:
                        del self._rooms[key]

    async def broadcast_now(
        self, room_keys: tuple[str, ...] | list[str], payload: dict[str, Any]
    ) -> None:
        async with self._lock:
            targets: list[WebSocket] = []
            seen: set[int] = set()
            for room_key in room_keys:
                for socket in self._rooms.get(room_key, set()):
                    marker = id(socket)
                    if marker in seen:
                        continue
                    seen.add(marker)
                    targets.append(socket)
        for socket in targets:
            await self._send(socket, payload)

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await asyncio.wait_for(
                websocket.send_json(payload),
                timeout=SEND_TIMEOUT_SECONDS,
            )
        except Exception:  # noqa: BLE001
            await self.disconnect(websocket)
            with contextlib.suppress(Exception):
                await websocket.close(code=1011)


_hub: InMemoryInvoicePostingRealtimeHub | None = None


def get_invoice_posting_realtime_hub() -> InMemoryInvoicePostingRealtimeHub | None:
    return _hub


def set_invoice_posting_realtime_hub(
    hub: InMemoryInvoicePostingRealtimeHub | None,
) -> None:
    global _hub
    _hub = hub
