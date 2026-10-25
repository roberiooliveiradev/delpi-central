"""Rotas self-only — Minhas tarefas (RQ-TASK-01..07) e perfil corporativo.

- ``GET /me/tasks``: TaskProjection composta on-read dos owners P4/P5 —
  nunca TaskEntity paralela (doc 27 §2, §12); sempre self-only.
- ``GET /me/profile``: dados corporativos do próprio usuário via proxy
  read-through do Core ``/me/person-profile`` + grupos/permissões já
  resolvidas pelo middleware compartilhado. Nunca cadastro paralelo.
"""

import httpx
from fastapi import APIRouter, Request

from controllership_finance_app.config import settings

from delpi_auth.authz_core import has_permission

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.closing_tasks_repository import (
    ClosingTasksRepository,
)

ACCESS_PERMISSION = "controllership-finance.access"

router = APIRouter(prefix="/me", tags=["My Tasks"])


def _require_user(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")
    return user


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        operation_id=operation_id,
    )


@router.get("/tasks", operation_id="list_my_tasks")
def list_my_tasks(request: Request, period: str | None = None):
    user = _require_user(request)
    try:
        projection = ClosingTasksRepository().list_my_tasks(
            subject=str(user.id),
            user_groups=getattr(user, "groups", []) or [],
            period=period,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_my_tasks")
    return ok(projection, operation_id="list_my_tasks")


@router.get("/profile", operation_id="get_my_profile")
async def get_my_profile(request: Request):
    """Perfil corporativo do próprio usuário (read-through, self-only)."""
    user = _require_user(request)
    profile: dict = {
        "id": str(user.id),
        "displayName": getattr(user, "name", None),
        "email": getattr(user, "email", None),
        "groups": getattr(user, "groups", []) or [],
        "permissions": getattr(user, "permissions", []) or [],
    }
    # Enriquecimento corporativo via Core — Bearer do usuário,
    # read-only, sem cache sensível em escrita.
    bearer = request.headers.get("Authorization", "")
    if bearer.startswith("Bearer "):
        url = settings.CORE_API_BASE_URL.rstrip("/") + "/me/person-profile"
        try:
            async with httpx.AsyncClient(
                timeout=5.0, follow_redirects=False
            ) as client:
                upstream = await client.get(
                    url, headers={"Authorization": bearer}
                )
            if upstream.status_code == 200:
                body = upstream.json()
                profile["personProfile"] = body.get(
                    "personProfile", body
                )
            else:
                profile["personProfile"] = None
        except (httpx.RequestError, ValueError):
            profile["personProfile"] = None
    else:
        profile["personProfile"] = None
    return ok(profile, operation_id="get_my_profile")
