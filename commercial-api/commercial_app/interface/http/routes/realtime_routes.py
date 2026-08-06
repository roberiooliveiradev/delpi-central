from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from delpi_auth.jwt_validator import validate_token

from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_WORKLIST_PERMISSIONS,
    can_manage_portfolios,
    has_any_permission,
)
from commercial_app.application.services.commercial_realtime_hub import (
    commercial_realtime_hub,
)
from commercial_app.application.services.commercial_realtime_notify import (
    TEAM_ROOM,
    user_room,
)

router = APIRouter(prefix="/commercial/realtime", tags=["Comercial — tempo real"])


def _actor_sub(payload: dict) -> str | None:
    sub = payload.get("sub")
    return str(sub).strip() if sub else None


@router.websocket("/ws")
async def commercial_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    try:
        payload = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc

    if not isinstance(payload, dict):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user_id = _actor_sub(payload)
    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if not has_any_permission(payload, COMMERCIAL_WORKLIST_PERMISSIONS):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    room_keys = [user_room(user_id)]
    if can_manage_portfolios(payload):
        room_keys.append(TEAM_ROOM)

    await commercial_realtime_hub.connect(
        websocket,
        room_keys=room_keys,
        user_id=user_id,
        client_id=client_id,
    )
