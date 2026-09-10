"""Protocolo WS: subscribe/unsubscribe em request:{uuid}."""

from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from fastapi import WebSocket

from requests_app.application.services.requests_realtime_hub import RequestsRealtimeHub
from requests_app.application.services.requests_realtime_notify import request_room


def parse_request_subscription(raw: str) -> tuple[str, str] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    action = str(payload.get("type") or "").strip().lower()
    if action not in {"subscribe", "unsubscribe"}:
        return None
    request_id = str(
        payload.get("requestId")
        or payload.get("request_id")
        or payload.get("roomId")
        or payload.get("room_id")
        or ""
    ).strip()
    if not request_id:
        return None
    return action, request_id


def _valid_request_uuid(request_id: str) -> str | None:
    try:
        return str(UUID(request_id))
    except (TypeError, ValueError):
        return None


async def handle_realtime_client_message(
    *,
    hub: RequestsRealtimeHub,
    websocket: WebSocket,
    user_id: str,
    raw: str,
    can_join_request: Callable[[str, str], bool],
) -> dict[str, Any] | None:
    parsed = parse_request_subscription(raw)
    if parsed is None:
        return None
    action, request_id_raw = parsed
    request_id = _valid_request_uuid(request_id_raw)
    if request_id is None:
        ack = {"type": "error", "code": "requestIdInvalid"}
        await websocket.send_json(ack)
        return ack
    room_key = request_room(request_id)
    if action == "subscribe":
        if not can_join_request(user_id, request_id):
            ack = {
                "type": "error",
                "code": "accessDenied",
                "requestId": request_id,
            }
            await websocket.send_json(ack)
            return ack
        joined = await hub.join_room(websocket, room_key)
        ack = {
            "type": "subscribed" if joined else "error",
            "code": None if joined else "subscribeFailed",
            "requestId": request_id,
            "roomKey": room_key,
        }
        await websocket.send_json(ack)
        return ack
    left = await hub.leave_room(websocket, room_key)
    ack = {
        "type": "unsubscribed" if left else "error",
        "code": None if left else "unsubscribeFailed",
        "requestId": request_id,
        "roomKey": room_key,
    }
    await websocket.send_json(ack)
    return ack
