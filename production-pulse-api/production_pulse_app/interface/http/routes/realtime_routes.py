from __future__ import annotations

import logging
from types import SimpleNamespace
from uuid import UUID

from delpi_auth.authz_core import has_permission
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import _rbac_from_claims, load_user_rbac
from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from production_pulse_app.application.security.production_pulse_permissions import (
    ACCESS,
    ADMIN,
    DEVICES_VIEW,
    branch_codes_for_access,
    can_view_devices,
)
from production_pulse_app.application.services.production_pulse_realtime_hub import (
    production_pulse_realtime_hub,
)
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    branch_room,
    user_room,
)
from production_pulse_app.application.services.production_pulse_realtime_protocol import (
    handle_realtime_client_message,
)
from production_pulse_app.config import settings
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareUpdateJobRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/realtime", tags=["Production Pulse — tempo real"])


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
        logger.warning("production_pulse_realtime_rbac_unavailable", exc_info=True)
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
        has_permission(user, ACCESS)
        or has_permission(user, ADMIN)
        or has_permission(user, DEVICES_VIEW)
        or can_view_devices(user)
    ):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user.id = user_id
    return user


def can_subscribe_device(user: SimpleNamespace, device_id: str) -> bool:
    if not can_view_devices(user):
        return False
    try:
        parsed = UUID(str(device_id or "").strip())
    except (TypeError, ValueError):
        return False
    device = PostgresDeviceRepository().get_by_id(parsed)
    if device is None:
        return False
    branch = str(device.get("branch") or "").strip()
    return branch in branch_codes_for_access(user)


def can_subscribe_ota_job(user: SimpleNamespace, job_id: str) -> bool:
    if not can_view_devices(user):
        return False
    try:
        parsed = UUID(str(job_id or "").strip())
    except (TypeError, ValueError):
        return False
    job = PostgresFirmwareUpdateJobRepository().get_job(parsed)
    if job is None:
        return False
    branch = str(job.get("branch") or "").strip()
    return branch in branch_codes_for_access(user)


@router.websocket("/ws")
async def production_pulse_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    if not settings.PP_REALTIME_ENABLED:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user = await resolve_websocket_user(token)
    user_id = str(user.id)

    room_keys = [user_room(user_id)]
    if can_view_devices(user):
        for code in branch_codes_for_access(user):
            room_keys.append(branch_room(code))

    async def on_text(socket: WebSocket, raw: str) -> None:
        await handle_realtime_client_message(
            hub=production_pulse_realtime_hub,
            websocket=socket,
            user_id=user_id,
            raw=raw,
            can_join_device=lambda _uid, did: can_subscribe_device(user, did),
            can_join_ota_job=lambda _uid, jid: can_subscribe_ota_job(user, jid),
        )

    await production_pulse_realtime_hub.connect(
        websocket,
        room_keys=room_keys,
        user_id=user_id,
        client_id=client_id,
        on_text=on_text,
    )
