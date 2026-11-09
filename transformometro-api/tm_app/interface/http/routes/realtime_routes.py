from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import load_user_rbac

from tm_app.application.security.authorization_policy import (
    TransformometroAuthorizationPolicy,
)
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
from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)

router = APIRouter(prefix="/transformometro/realtime", tags=["Transformômetro — tempo real"])

_authz = TransformometroAuthorizationPolicy()


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


def _user_from_rbac(claims: dict, rbac: dict, token: str) -> SimpleNamespace:
    sub = claims.get("sub")
    email = claims.get("email")
    return SimpleNamespace(
        id=rbac.get("id") or sub,
        email=rbac.get("email") or email,
        name=rbac.get("name") or claims.get("name") or email or "Usuário",
        roles=rbac.get("roles", []),
        groups=rbac.get("groups", []),
        permissions=rbac.get("permissions", []),
        is_superadmin=rbac.get("is_superadmin", False),
        rbac_unavailable=bool(rbac.get("rbac_unavailable")),
        access_token=token,
        principal_type="user",
    )


async def _authorize_realtime_join(
    *,
    token: str,
    claims: dict,
    entity_type: str,
    entity_id: str,
) -> SimpleNamespace:
    """JWT is not enough — require transformometro.access (+ resource for atas)."""
    try:
        rbac = await load_user_rbac(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc

    user = _user_from_rbac(claims, rbac, token)
    if not _authz.has_access(user):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if entity_type == "meeting_minute":
        try:
            UUID(str(entity_id))
        except (TypeError, ValueError) as exc:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
        minute = MeetingMinuteRepository().get_minute(str(entity_id))
        if not minute:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if entity_type == "catalog" and str(entity_id) == "meeting_minute":
        # Catalog room: domain access already checked above.
        return user

    return user


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

    await _authorize_realtime_join(
        token=token,
        claims=payload,
        entity_type=entity_type,
        entity_id=entity_id,
    )

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
