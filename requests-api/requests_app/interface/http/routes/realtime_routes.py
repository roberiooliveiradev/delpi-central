from __future__ import annotations

import logging
from types import SimpleNamespace
from uuid import UUID

from delpi_auth.authz_core import has_permission
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import _rbac_from_claims, load_user_rbac
from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from requests_app.application.security.requests_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
    VIEW_ALL_PERMISSION,
    actor_for,
    has_branch_access,
)
from requests_app.application.services.requests_realtime_hub import requests_realtime_hub
from requests_app.application.services.requests_realtime_notify import (
    WORK_QUEUE_ROOM,
    user_room,
)
from requests_app.application.services.requests_realtime_protocol import (
    handle_realtime_client_message,
)
from requests_app.composition.requests_composer import (
    build_request_repository,
    build_request_type_repository,
)
from requests_app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/realtime", tags=["Minhas Solicitações — tempo real"])


def _can_join_work_queue(user) -> bool:
    if has_permission(user, VIEW_ALL_PERMISSION) or has_permission(user, MANAGE_PERMISSION):
        return True
    for raw in getattr(user, "permissions", None) or []:
        perm = str(raw or "").strip()
        if perm.startswith("my-requests.") and perm.endswith(".process"):
            return True
    return False


async def resolve_websocket_user(token: str) -> SimpleNamespace:
    """JWT válido + RBAC via core-api (permissões não vêm no access token Keycloak)."""
    try:
        claims = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc

    if not isinstance(claims, dict):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        rbac = await load_user_rbac(token)
    except Exception:
        logger.warning("requests_realtime_rbac_unavailable", exc_info=True)
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
        has_permission(user, ACCESS_PERMISSION)
        or has_permission(user, VIEW_ALL_PERMISSION)
        or has_permission(user, MANAGE_PERMISSION)
    ):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user.id = user_id
    return user


def can_subscribe_request(user: SimpleNamespace, request_id: str) -> bool:
    try:
        parsed = UUID(str(request_id or "").strip())
    except (TypeError, ValueError):
        return False
    request = build_request_repository().get(str(parsed))
    if request is None:
        return False
    request_type = build_request_type_repository().get_by_code(request.type_code)
    if request_type is None:
        return False
    actor = actor_for(user, request_type)
    is_owner = request.created_by_user_id == actor.user_id
    if not (is_owner or actor.has_view_all or actor.has_process or actor.has_manage):
        return False
    if request.branch_code and not has_branch_access(actor, request.branch_code):
        if not is_owner:
            return False
    return True


@router.websocket("/ws")
async def requests_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    if not settings.REQUESTS_REALTIME_ENABLED:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user = await resolve_websocket_user(token)
    user_id = str(user.id)

    room_keys = [user_room(user_id)]
    if _can_join_work_queue(user):
        room_keys.append(WORK_QUEUE_ROOM)

    async def on_text(socket: WebSocket, raw: str) -> None:
        await handle_realtime_client_message(
            hub=requests_realtime_hub,
            websocket=socket,
            user_id=user_id,
            raw=raw,
            can_join_request=lambda _uid, rid: can_subscribe_request(user, rid),
        )

    await requests_realtime_hub.connect(
        websocket,
        room_keys=room_keys,
        user_id=user_id,
        client_id=client_id,
        on_text=on_text,
    )
