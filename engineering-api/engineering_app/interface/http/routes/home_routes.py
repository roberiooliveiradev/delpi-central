"""Rota de negócio da Home do Portal Engenharia (F2a.S4).

`GET /v1/home` — composição autorizada. AuthZ:
- `require_any_permission(["engineering.access"])` — permissão efetiva
  resolvida pela Core via delpi_auth (fail-closed enquanto a permissão
  não estiver registrada — G5 activation gate).
- `principal_type == "user"` — Home personalizada é rota humana; service
  principals não recebem Home como se fossem usuários.
"""

from __future__ import annotations

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.composition.home_composer import (
    build_get_engineering_home_use_case,
)
from engineering_app.core.responses import fail, ok
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

ENGINEERING_ACCESS = "engineering.access"
_OPERATION_ID = "get_engineering_home"


@router.get(
    "/v1/home",
    operation_id="get_engineering_home",
    summary="Home do Portal Engenharia — composição autorizada",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_engineering_home():
    user = resolve_user_context()

    if getattr(user, "principal_type", None) != "user":
        return fail(
            "A Home personalizada exige principal humano.",
            403,
            operation_id=_OPERATION_ID,
        )

    ctx = HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    )
    home = await build_get_engineering_home_use_case().execute(ctx)
    return ok(
        home.model_dump(),
        message="Home do Portal Engenharia.",
        operation_id=_OPERATION_ID,
    )
