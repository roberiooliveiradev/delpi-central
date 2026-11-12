"""Protocolo WS Engineering — subscribe/unsubscribe por domínio/recurso.

Envelope cliente:
    {"type":"subscribe","domain":"product-registration",
     "resourceType":"request","resourceId":"<uuid>"}
    {"type":"unsubscribe", ...}

Acks: ``subscribed`` | ``unsubscribed`` | ``error``
(codes: ``messageInvalid``, ``resourceIdInvalid``, ``domainUnsupported``,
``accessDenied``, ``subscribeFailed``, ``unsubscribeFailed``).
"""

from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from fastapi import WebSocket

from engineering_app.application.services.engineering_realtime_hub import (
    EngineeringRealtimeHub,
    RoomAuthorizer,
)
from engineering_app.application.services.engineering_realtime_notify import (
    resource_room,
)

_MAX_MESSAGE_BYTES = 4096


def parse_subscription(raw: str) -> tuple[str, str, str, str] | None:
    if len(raw) > _MAX_MESSAGE_BYTES:
        return ("__invalid__", "", "", "")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    action = str(payload.get("type") or "").strip().lower()
    if action not in {"subscribe", "unsubscribe"}:
        return None
    domain = str(payload.get("domain") or "").strip()
    resource_type = str(payload.get("resourceType") or "").strip() or "request"
    resource_id = str(
        payload.get("resourceId")
        or payload.get("resource_id")
        or payload.get("roomId")
        or ""
    ).strip()
    if not domain or not resource_id:
        return ("__invalid__", domain, resource_type, resource_id)
    return action, domain, resource_type, resource_id


def _valid_uuid(value: str) -> str | None:
    try:
        return str(UUID(value))
    except (TypeError, ValueError):
        return None


def _ack(socket_payload: dict[str, Any]) -> dict[str, Any]:
    return socket_payload


async def handle_client_message(
    *,
    hub: EngineeringRealtimeHub,
    websocket: WebSocket,
    raw: str,
    resolve_authorizer: Callable[
        [str, str], tuple[RoomAuthorizer | None, str | None]
    ],
) -> dict[str, Any] | None:
    """``resolve_authorizer(domain, resource_id)`` devolve
    ``(authorizer, None)`` ou ``(None, error_code)``."""
    parsed = parse_subscription(raw)
    if parsed is None:
        return None
    action, domain, resource_type, resource_id = parsed
    if action == "__invalid__":
        ack = {"type": "error", "code": "messageInvalid"}
        await websocket.send_json(ack)
        return ack
    rid = _valid_uuid(resource_id)
    if rid is None:
        ack = {
            "type": "error",
            "code": "resourceIdInvalid",
            "domain": domain,
            "resourceId": resource_id,
        }
        await websocket.send_json(ack)
        return ack
    authorizer, denial_code = resolve_authorizer(domain, rid)
    if authorizer is None:
        ack = {
            "type": "error",
            "code": denial_code or "accessDenied",
            "domain": domain,
            "resourceId": rid,
        }
        await websocket.send_json(ack)
        return ack
    room_key = resource_room(domain, rid)
    if action == "subscribe":
        joined = await hub.join_room(
            websocket, room_key, authorizer=authorizer
        )
        ack = {
            "type": "subscribed" if joined else "error",
            "code": None if joined else "subscribeFailed",
            "domain": domain,
            "resourceType": resource_type,
            "resourceId": rid,
            "roomKey": room_key,
        }
        await websocket.send_json(ack)
        return ack
    left = await hub.leave_room(websocket, room_key)
    ack = {
        "type": "unsubscribed" if left else "error",
        "code": None if left else "unsubscribeFailed",
        "domain": domain,
        "resourceType": resource_type,
        "resourceId": rid,
        "roomKey": room_key,
    }
    await websocket.send_json(ack)
    return ack
