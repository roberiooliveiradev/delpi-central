from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from delpi_auth.jwt_validator import validate_token

from tm_app.application.services.transformometro_realtime_hub import (
    transformometro_realtime_hub,
)
from tm_app.application.services.transformometro_realtime_notify import room_key
from tm_app.infrastructure.persistence.repositories.collaboration_presence_repository import (
    ALLOWED_ENTITY_TYPES,
)

router = APIRouter(prefix="/transformometro/realtime", tags=["Transformômetro — tempo real"])


@router.websocket("/ws")
async def transformometro_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    entity_type: str = Query(..., min_length=1),
    entity_id: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        payload = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    await transformometro_realtime_hub.connect(
        websocket,
        room_key=room_key(entity_type, entity_id),
        user_id=str(user_id),
        client_id=client_id,
    )
