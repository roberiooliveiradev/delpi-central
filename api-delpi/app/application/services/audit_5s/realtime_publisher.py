from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.interface.socket.sio_server import sio


def _room(audit_id: str) -> str:
    return f"audit:{audit_id}"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value


async def publish_response_updated(
    *,
    audit_id: str,
    response: dict[str, Any],
    audit: dict[str, Any],
    actor_user_id: str,
    actor_display_name: str,
) -> None:
    payload = _json_safe(
        {
            "audit_id": audit_id,
            "response": response,
            "audit": audit,
            "actor_user_id": actor_user_id,
            "actor_display_name": actor_display_name,
        },
    )
    await sio.emit("audit5s.response.updated", payload, room=_room(audit_id))


async def publish_audit_updated(
    *,
    audit_id: str,
    audit: dict[str, Any],
    event_type: str,
    actor_user_id: str,
    actor_display_name: str,
) -> None:
    payload = _json_safe(
        {
            "audit_id": audit_id,
            "audit": audit,
            "event_type": event_type,
            "actor_user_id": actor_user_id,
            "actor_display_name": actor_display_name,
        },
    )
    await sio.emit("audit5s.audit.updated", payload, room=_room(audit_id))
