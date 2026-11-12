"""WebSocket transversal Engineering API — ENG-REALTIME-01.

Endpoint: ``/v1/realtime/ws?token={jwt}&client_id={id}``

AuthN fail-closed no handler (o middleware JWT é ``http``-scope e não
cobra WebSocket): JWT válido via ``delpi_auth`` + RBAC Core
(``load_user_rbac``) — mesmo padrão do realtime da Requests API.

AuthZ:
- ``user:{sub}`` — sempre (identidade própria);
- ``queue:{domain}`` — somente analista (``engineering.access``);
- ``res:{domain}:{id}`` — assinatura autorizada pelo adapter do domínio
  (PRC: leitura do módulo + escopo por objeto) com revalidação a cada
  entrega (revogação por objeto em conexão ativa).
"""

from __future__ import annotations

import logging
import time
from types import SimpleNamespace

from delpi_auth.authz_core import has_permission
from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware import fastapi_auth
from delpi_auth.middleware.fastapi_auth import _rbac_from_claims
from fastapi import APIRouter, Query, WebSocket, WebSocketException, status

from engineering_app.application.services.engineering_realtime_hub import (
    engineering_realtime_hub,
)
from engineering_app.application.services.engineering_realtime_notify import (
    queue_room,
    user_room,
)
from engineering_app.application.services.engineering_realtime_protocol import (
    handle_client_message,
)
from engineering_app.application.use_cases.product_registration.actor import (
    prc_actor_from_principal,
)
from engineering_app.composition.prc_composer import build_prc_service
from engineering_app.config import settings
from engineering_app.domain.product_registration.models import (
    ENG_ACCESS,
    MR_ACCESS,
    MR_PRC_CREATE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/realtime", tags=["Engenharia — tempo real"])

PRC_DOMAIN = "product-registration"
_SUPPORTED_DOMAINS = frozenset({PRC_DOMAIN})

_REALTIME_PERMISSIONS = (ENG_ACCESS, MR_ACCESS, MR_PRC_CREATE)


async def resolve_websocket_user(token: str) -> tuple[SimpleNamespace, dict]:
    """JWT válido + RBAC Core — fail-closed, principal humano."""
    try:
        claims = validate_token(token)
    except Exception as exc:  # noqa: BLE001
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
    if not isinstance(claims, dict):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        rbac = await fastapi_auth.load_user_rbac(token)
    except Exception:
        logger.warning("engineering_realtime_rbac_unavailable", exc_info=True)
        rbac = _rbac_from_claims(claims, token, rbac_unavailable=True)

    user = SimpleNamespace(
        id=rbac.get("id") or claims.get("sub"),
        email=rbac.get("email") or claims.get("email"),
        name=rbac.get("name") or claims.get("name") or claims.get("email"),
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

    if not any(has_permission(user, code) for code in _REALTIME_PERMISSIONS):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user.id = user_id
    return user, claims


def _prc_authorizer(user: SimpleNamespace, resource_id: str):
    """Authorizer por-entrega — reexecuta ``can_observe`` (escopo vivo do
    objeto) antes de cada evento entregue ao socket."""
    service = build_prc_service()
    actor = prc_actor_from_principal(user, channel="realtime")

    def authorize() -> bool:
        return service.can_observe(resource_id, actor)

    return authorize


@router.websocket("/ws")
async def engineering_realtime_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=1),
    client_id: str = Query(""),
):
    if not settings.ENG_REALTIME_ENABLED:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user, claims = await resolve_websocket_user(token)
    user_id = str(user.id)
    actor = prc_actor_from_principal(user, channel="realtime")

    room_keys = [user_room(user_id)]
    if actor.is_analyst:
        room_keys.append(queue_room(PRC_DOMAIN))

    def resolve_authorizer(domain: str, resource_id: str):
        if domain not in _SUPPORTED_DOMAINS:
            return None, "domainUnsupported"
        if _prc_authorizer(user, resource_id)():
            return _prc_authorizer(user, resource_id), None
        return None, "accessDenied"

    async def on_text(socket: WebSocket, raw: str) -> None:
        await handle_client_message(
            hub=engineering_realtime_hub,
            websocket=socket,
            raw=raw,
            resolve_authorizer=resolve_authorizer,
        )

    exp = claims.get("exp")
    close_after = None
    if isinstance(exp, (int, float)):
        close_after = max(0.0, float(exp) - time.time()) + 5.0

    await engineering_realtime_hub.connect(
        websocket,
        room_keys=room_keys,
        user_id=user_id,
        client_id=client_id,
        on_text=on_text,
        close_after_seconds=close_after,
    )
