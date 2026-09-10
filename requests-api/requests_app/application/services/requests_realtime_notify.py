"""Fan-out de eventos leves para o hub WebSocket de Minhas Solicitações."""

from __future__ import annotations

import logging
from typing import Any

from requests_app.application.services.requests_realtime_hub import requests_realtime_hub
from requests_app.config import settings

logger = logging.getLogger(__name__)

WORK_QUEUE_ROOM = "work-queue"


def user_room(user_id: str) -> str:
    return f"user:{user_id.strip()}"


def request_room(request_id: str) -> str:
    return f"request:{str(request_id or '').strip()}"


def _realtime_enabled() -> bool:
    return bool(settings.REQUESTS_REALTIME_ENABLED)


def _broadcast_rooms(room_keys: list[str], payload: dict[str, Any]) -> None:
    if not _realtime_enabled():
        return
    try:
        requests_realtime_hub.schedule_broadcast_rooms(room_keys, payload)
    except Exception:  # noqa: BLE001
        logger.exception("requests_realtime_schedule_failed rooms=%s", room_keys)


def _unique_rooms(*candidates: str | None) -> list[str]:
    seen: set[str] = set()
    rooms: list[str] = []
    for raw in candidates:
        key = str(raw or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        rooms.append(key)
    return rooms


def _party_user_rooms(
    *,
    owner_user_id: str | None = None,
    assignee_user_id: str | None = None,
) -> list[str]:
    rooms: list[str] = []
    owner = str(owner_user_id or "").strip()
    if owner:
        rooms.append(user_room(owner))
    assignee = str(assignee_user_id or "").strip()
    if assignee:
        rooms.append(user_room(assignee))
    return rooms


def _base_payload(
    *,
    event_type: str,
    reason: str,
    request_id: str,
    request_number: str | None = None,
    status: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
    owner_user_id: str | None = None,
    assignee_user_id: str | None = None,
    notification: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": event_type,
        "reason": reason,
        "requestId": str(request_id),
        "requestNumber": (request_number or "").strip() or None,
        "status": (status or "").strip() or None,
        "actorUserId": (actor_user_id or "").strip() or None,
        "actorClientId": (actor_client_id or "").strip() or None,
        "ownerUserId": (owner_user_id or "").strip() or None,
        "assigneeUserId": (assignee_user_id or "").strip() or None,
    }
    if notification:
        payload["notification"] = notification
    return payload


def notify_request_created(
    *,
    request_id: str,
    request_number: str | None = None,
    status: str | None = None,
    owner_user_id: str | None = None,
    assignee_user_id: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
    notification: dict[str, str] | None = None,
) -> None:
    payload = _base_payload(
        event_type="request.created",
        reason="create",
        request_id=request_id,
        request_number=request_number,
        status=status,
        actor_user_id=actor_user_id,
        actor_client_id=actor_client_id,
        owner_user_id=owner_user_id,
        assignee_user_id=assignee_user_id,
        notification=notification,
    )
    rooms = _unique_rooms(
        WORK_QUEUE_ROOM,
        *_party_user_rooms(
            owner_user_id=owner_user_id,
            assignee_user_id=assignee_user_id,
        ),
    )
    _broadcast_rooms(rooms, payload)


def notify_request_changed(
    *,
    reason: str,
    request_id: str,
    request_number: str | None = None,
    status: str | None = None,
    owner_user_id: str | None = None,
    assignee_user_id: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
    notification: dict[str, str] | None = None,
) -> None:
    payload = _base_payload(
        event_type="request.changed",
        reason=reason,
        request_id=request_id,
        request_number=request_number,
        status=status,
        actor_user_id=actor_user_id,
        actor_client_id=actor_client_id,
        owner_user_id=owner_user_id,
        assignee_user_id=assignee_user_id,
        notification=notification,
    )
    rooms = _unique_rooms(
        request_room(request_id),
        WORK_QUEUE_ROOM,
        *_party_user_rooms(
            owner_user_id=owner_user_id,
            assignee_user_id=assignee_user_id,
        ),
    )
    _broadcast_rooms(rooms, payload)


def notify_request_timeline(
    *,
    reason: str,
    request_id: str,
    request_number: str | None = None,
    status: str | None = None,
    owner_user_id: str | None = None,
    assignee_user_id: str | None = None,
    actor_user_id: str | None = None,
    actor_client_id: str | None = None,
    notification: dict[str, str] | None = None,
) -> None:
    payload = _base_payload(
        event_type="request.timeline",
        reason=reason,
        request_id=request_id,
        request_number=request_number,
        status=status,
        actor_user_id=actor_user_id,
        actor_client_id=actor_client_id,
        owner_user_id=owner_user_id,
        assignee_user_id=assignee_user_id,
        notification=notification,
    )
    rooms = _unique_rooms(
        request_room(request_id),
        *_party_user_rooms(
            owner_user_id=owner_user_id,
            assignee_user_id=assignee_user_id,
        ),
    )
    _broadcast_rooms(rooms, payload)
