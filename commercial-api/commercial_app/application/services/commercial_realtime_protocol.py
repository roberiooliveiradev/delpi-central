"""Protocolo WS da sala de interação no hub existente (subscribe/unsubscribe)."""

from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from fastapi import WebSocket

from commercial_app.application.services.commercial_realtime_hub import (
    CommercialRealtimeHub,
)
from commercial_app.application.services.commercial_realtime_notify import (
    interaction_room_key,
)


def parse_room_subscription(raw: str) -> tuple[str, str] | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    action = str(payload.get("type") or "").strip().lower()
    if action not in {"subscribe", "unsubscribe"}:
        return None
    room_id = str(payload.get("roomId") or payload.get("room_id") or "").strip()
    if not room_id:
        return None
    return action, room_id


def _valid_room_uuid(room_id: str) -> str | None:
    try:
        return str(UUID(room_id))
    except (TypeError, ValueError):
        return None


async def handle_realtime_client_message(
    *,
    hub: CommercialRealtimeHub,
    websocket: WebSocket,
    user_id: str,
    raw: str,
    can_join_room: Callable[[str, str], bool],
) -> dict[str, Any] | None:
    parsed = parse_room_subscription(raw)
    if parsed is None:
        return None
    action, room_id_raw = parsed
    room_id = _valid_room_uuid(room_id_raw)
    if room_id is None:
        ack = {"type": "error", "code": "roomIdInvalid"}
        await websocket.send_json(ack)
        return ack
    room_key = interaction_room_key(room_id)
    if action == "subscribe":
        if not can_join_room(user_id, room_id):
            ack = {
                "type": "error",
                "code": "accessDenied",
                "roomId": room_id,
            }
            await websocket.send_json(ack)
            return ack
        joined = await hub.join_room(websocket, room_key)
        ack = {
            "type": "subscribed" if joined else "error",
            "code": None if joined else "subscribeFailed",
            "roomId": room_id,
            "roomKey": room_key,
        }
        await websocket.send_json(ack)
        return ack
    left = await hub.leave_room(websocket, room_key)
    ack = {
        "type": "unsubscribed" if left else "error",
        "code": None if left else "unsubscribeFailed",
        "roomId": room_id,
        "roomKey": room_key,
    }
    await websocket.send_json(ack)
    return ack
