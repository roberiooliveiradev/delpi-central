from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from delpi_auth.jwt_validator import validate_token

from tm_app.application.services.transformometro_realtime_collaboration import (
    transformometro_realtime_collaboration,
)
from tm_app.application.services.transformometro_realtime_hub import (
    transformometro_realtime_hub,
)
from tm_app.application.services.transformometro_realtime_notify import room_key
from tm_app.infrastructure.persistence.repositories.collaboration_presence_repository import (
    ALLOWED_ENTITY_TYPES,
)

router = APIRouter(prefix="/transformometro/realtime", tags=["Transformômetro — tempo real"])


def _actor_from_token(payload: dict) -> tuple[str | None, str | None, str | None]:
    user_id = payload.get("sub")
    email = payload.get("email")
    user_name = payload.get("name") or payload.get("preferred_username")
    if isinstance(user_name, str) and email and user_name.lower() == str(email).lower():
        user_name = None
    return (
        str(user_id) if user_id else None,
        str(email) if email else None,
        str(user_name).strip() if isinstance(user_name, str) and user_name.strip() else None,
    )


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

    user_id, user_email, user_name = _actor_from_token(payload)
    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    entity_room = room_key(entity_type, entity_id)

    async def on_message(socket: WebSocket, message: str) -> None:
        await transformometro_realtime_collaboration.handle_message(
            socket,
            raw_message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
        )

    async def on_user_disconnect(_room_key: str, _user_id: str, remaining: int) -> None:
        await transformometro_realtime_collaboration.handle_disconnect(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            remaining_connections=remaining,
        )

    await transformometro_realtime_hub.connect(
        websocket,
        room_key=entity_room,
        user_id=user_id,
        client_id=client_id,
        on_message=on_message,
        on_user_disconnect=on_user_disconnect,
    )
