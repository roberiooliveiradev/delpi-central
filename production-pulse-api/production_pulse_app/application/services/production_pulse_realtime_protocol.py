"""Client→server protocol for Production Pulse realtime (optional room joins)."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable
from uuid import UUID

from fastapi import WebSocket

from production_pulse_app.application.services.production_pulse_realtime_hub import (
    ProductionPulseRealtimeHub,
)
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    device_room,
    ota_job_room,
)

logger = logging.getLogger(__name__)

CanJoinRoom = Callable[[str, str], bool]


def parse_room_subscription(raw: str) -> tuple[str, str, str] | None:
    """Return (action, kind, id) for subscribe/unsubscribe messages."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    action = str(data.get("type") or "").strip().lower()
    if action not in {"subscribe", "unsubscribe"}:
        return None
    device_id = str(
        data.get("deviceId") or data.get("device_id") or ""
    ).strip()
    job_id = str(
        data.get("jobId") or data.get("job_id") or data.get("otaJobId") or ""
    ).strip()
    if device_id:
        return action, "device", device_id
    if job_id:
        return action, "ota.job", job_id
    return None


async def handle_realtime_client_message(
    *,
    hub: ProductionPulseRealtimeHub,
    websocket: WebSocket,
    user_id: str,
    raw: str,
    can_join_device: CanJoinRoom,
    can_join_ota_job: CanJoinRoom,
) -> dict[str, Any] | None:
    parsed = parse_room_subscription(raw)
    if parsed is None:
        await websocket.send_json(
            {"type": "error", "code": "invalid_message"}
        )
        return None

    action, kind, entity_id = parsed
    try:
        UUID(entity_id)
    except (TypeError, ValueError):
        await websocket.send_json(
            {
                "type": "error",
                "code": "invalid_id",
                "deviceId": entity_id if kind == "device" else None,
                "jobId": entity_id if kind == "ota.job" else None,
            }
        )
        return None

    if kind == "device":
        room_key = device_room(entity_id)
        allowed = can_join_device(user_id, entity_id)
        ack_key = "deviceId"
    else:
        room_key = ota_job_room(entity_id)
        allowed = can_join_ota_job(user_id, entity_id)
        ack_key = "jobId"

    if not allowed:
        await websocket.send_json(
            {"type": "error", "code": "forbidden", ack_key: entity_id}
        )
        return None

    if action == "subscribe":
        ok = await hub.join_room(websocket, room_key)
        if not ok:
            await websocket.send_json(
                {"type": "error", "code": "not_connected", ack_key: entity_id}
            )
            return None
        payload = {"type": "subscribed", "roomKey": room_key, ack_key: entity_id}
        await websocket.send_json(payload)
        return payload

    ok = await hub.leave_room(websocket, room_key)
    if not ok:
        await websocket.send_json(
            {"type": "error", "code": "not_connected", ack_key: entity_id}
        )
        return None
    payload = {"type": "unsubscribed", "roomKey": room_key, ack_key: entity_id}
    await websocket.send_json(payload)
    return payload
