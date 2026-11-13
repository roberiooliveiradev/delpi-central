"""WebSocket do LNF. O middleware HTTP não cobre este escopo.

Montar esta rota só com LNF_HOSTED_ENABLED e LNF_REALTIME_ENABLED.
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
from types import SimpleNamespace
from urllib.parse import urlparse
from uuid import UUID

from delpi_auth.authz_core import has_permission
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware import fastapi_auth
from delpi_auth.middleware.fastapi_auth import _rbac_from_claims
from delpi_auth.request_context import set_current_user
from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS,
    LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS,
)
from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.invoice_posting.realtime_hub import (
    UNMAPPED_ROOM,
    get_invoice_posting_realtime_hub,
)
from controllership_finance_app.interface.http.routes.invoice_posting.branch_access import (
    branch_view_allowed,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lancamento-notas-fiscais", tags=["Lançamento de Notas Fiscais"])

_HANDSHAKE_PERMISSIONS = (
    *LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS,
    LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS,
)
_BRANCH_ROOMS = {"lnf:branch:01": "01", "lnf:branch:02": "02"}
_REQUEST_PREFIX = "lnf:request:"


def _portal_host() -> str:
    return urlparse(settings.PUBLIC_BASE_URL or "").netloc.lower()


def origin_allowed(origin: str | None) -> bool:
    expected = _portal_host()
    if not expected or not origin:
        return False
    return urlparse(origin).netloc.lower() == expected


def lookup_request_branch(request_id: str) -> str | None:
    from controllership_finance_app.application.invoice_posting.composer import (
        build_invoice_posting_request_repository,
    )

    row = build_invoice_posting_request_repository().get_request(request_id)
    if not row:
        return None
    branch = str(row.get("branch_code") or "").strip()
    return branch or None


async def _resolve_user(token: str) -> tuple[SimpleNamespace, dict]:
    try:
        claims = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
    if not isinstance(claims, dict):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or float(exp) <= time.time():
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    try:
        rbac = await fastapi_auth.load_user_rbac(token)
    except Exception:
        logger.warning("lnf_realtime_rbac_unavailable")
        rbac = _rbac_from_claims(claims, token, rbac_unavailable=True)
    user = SimpleNamespace(
        id=str(rbac.get("id") or claims.get("sub") or "").strip(),
        email=rbac.get("email") or claims.get("email"),
        name=rbac.get("name") or claims.get("name") or claims.get("email"),
        roles=list(rbac.get("roles") or []),
        groups=list(rbac.get("groups") or []),
        permissions=list(rbac.get("permissions") or []),
        is_superadmin=bool(rbac.get("is_superadmin")),
        rbac_unavailable=bool(rbac.get("rbac_unavailable")),
    )
    if not user.id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    if not any(has_permission(user, code) for code in _HANDSHAKE_PERMISSIONS):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return user, claims


def room_error(room: str) -> str | None:
    """None quando a sala pode ser assinada. Não revela solicitação inexistente."""
    if room in _BRANCH_ROOMS:
        if branch_view_allowed(_BRANCH_ROOMS[room]):
            return None
        return "forbidden_room"
    if room == UNMAPPED_ROOM:
        user = None
        from delpi_auth.request_context import get_current_user

        user = get_current_user()
        if user is not None and has_permission(
            user, LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS
        ):
            return None
        return "forbidden_room"
    if room.startswith(_REQUEST_PREFIX):
        raw_id = room[len(_REQUEST_PREFIX) :].strip()
        try:
            request_id = str(UUID(raw_id))
        except ValueError:
            return "unknown_room"
        try:
            branch = lookup_request_branch(request_id)
        except Exception:
            logger.warning("lnf_realtime_request_lookup_failed")
            raise
        if branch is None or not branch_view_allowed(branch):
            return "forbidden_room"
        return None
    return "unknown_room"


async def _handle_text(websocket: WebSocket, raw: str) -> None:
    hub = get_invoice_posting_realtime_hub()
    if hub is None:
        return
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_json(
            {"type": "error", "code": "unknown_room", "room": ""}
        )
        return
    if not isinstance(message, dict):
        await websocket.send_json(
            {"type": "error", "code": "unknown_room", "room": ""}
        )
        return
    kind = message.get("type")
    room = str(message.get("room") or "")
    if kind == "unsubscribe":
        await hub.leave(websocket, room)
        await websocket.send_json({"type": "unsubscribed", "room": room})
        return
    if kind != "subscribe":
        await websocket.send_json(
            {"type": "error", "code": "unknown_room", "room": room}
        )
        return
    try:
        error = room_error(room)
    except Exception:
        logger.warning("lnf_realtime_room_check_failed")
        with contextlib.suppress(Exception):
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    if error:
        await websocket.send_json({"type": "error", "code": error, "room": room})
        return
    await hub.join(websocket, room)
    await websocket.send_json({"type": "subscribed", "room": room})


@router.websocket("/realtime")
async def invoice_posting_realtime(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    origin = websocket.headers.get("origin")
    if not origin_allowed(origin):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user, claims = await _resolve_user(token)
    hub = get_invoice_posting_realtime_hub()
    if hub is None:
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR)
    user_token = set_current_user(user)
    exp = float(claims["exp"])
    close_after = max(0.0, exp - time.time()) + 5.0
    try:
        await hub.connect(
            websocket,
            on_text=_handle_text,
            close_after_seconds=close_after,
        )
    finally:
        from delpi_auth.request_context import reset_current_user

        reset_current_user(user_token)
