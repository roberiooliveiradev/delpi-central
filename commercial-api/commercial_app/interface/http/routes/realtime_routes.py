from __future__ import annotations

import logging
from types import SimpleNamespace

from fastapi import APIRouter, Query, WebSocket, WebSocketException, status
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import _rbac_from_claims, load_user_rbac

from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_READ_PERMISSIONS,
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/commercial/realtime", tags=["Comercial — tempo real"])


async def resolve_websocket_user(token: str) -> SimpleNamespace:
    """
    Autentica WS com o mesmo critério do middleware HTTP:
    JWT válido + RBAC via core-api (permissões não vêm no access token Keycloak).
    """
    try:
        claims = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc

    if not isinstance(claims, dict):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        rbac = await load_user_rbac(token)
    except Exception:
        logger.warning("commercial_realtime_rbac_unavailable", exc_info=True)
        rbac = _rbac_from_claims(claims, token, rbac_unavailable=True)

    user = SimpleNamespace(
        id=rbac.get("id") or claims.get("sub"),
        email=rbac.get("email") or claims.get("email"),
        name=rbac.get("name") or claims.get("name") or claims.get("email") or "Usuário",
        roles=list(rbac.get("roles") or []),
        groups=list(rbac.get("groups") or []),
        permissions=list(rbac.get("permissions") or []),
        is_superadmin=bool(rbac.get("is_superadmin")),
        rbac_unavailable=bool(rbac.get("rbac_unavailable")),
        access_token=token,
    )

    user_id = str(user.id or "").strip()
    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if not (
        has_any_permission(user, COMMERCIAL_WORKLIST_PERMISSIONS)
        or has_any_permission(user, COMMERCIAL_READ_PERMISSIONS)
    ):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user.id = user_id
    return user


@router.websocket("/ws")
async def commercial_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    user = await resolve_websocket_user(token)
    user_id = str(user.id)

    room_keys = [user_room(user_id)]
    if can_manage_portfolios(user):
        room_keys.append(TEAM_ROOM)

    await commercial_realtime_hub.connect(
        websocket,
        room_keys=room_keys,
        user_id=user_id,
        client_id=client_id,
    )
