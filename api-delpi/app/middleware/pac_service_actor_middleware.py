"""Propaga ator PAC (GPT) em chamadas S2S com X-Delpi-Actor-*."""

from __future__ import annotations

import logging
from types import SimpleNamespace

from starlette.requests import Request

from delpi_auth.request_context import reset_current_user, set_current_user

logger = logging.getLogger(__name__)

_QUALITY_ACTION_PLANS_PREFIX = "/quality/action-plans"


async def pac_service_actor_middleware(request: Request, call_next):
    user = getattr(request.state, "user", None)
    actor_id = (request.headers.get("X-Delpi-Actor-Id") or "").strip()

    if (
        user is not None
        and getattr(user, "id", None) == "internal-service"
        and actor_id
        and request.url.path.startswith(_QUALITY_ACTION_PLANS_PREFIX)
    ):
        actor_name = (request.headers.get("X-Delpi-Actor-Name") or "").strip() or "Agente PAC"
        actor_email = (request.headers.get("X-Delpi-Actor-Email") or "").strip() or (
            f"{actor_id}@pac.delpi.internal"
        )
        actor_user = SimpleNamespace(
            id=actor_id,
            email=actor_email,
            name=actor_name,
            roles=list(getattr(user, "roles", []) or []),
            groups=list(getattr(user, "groups", []) or []),
            permissions=list(getattr(user, "permissions", []) or []),
            is_superadmin=getattr(user, "is_superadmin", True),
            access_token=getattr(user, "access_token", None),
        )
        request.state.user = actor_user
        context_token = set_current_user(actor_user)
        try:
            return await call_next(request)
        finally:
            reset_current_user(context_token)

    return await call_next(request)
