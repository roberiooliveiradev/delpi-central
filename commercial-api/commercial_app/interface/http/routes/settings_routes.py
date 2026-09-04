"""Settings — SLA policies CRUD (`/settings/sla-policies`)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    has_manage,
)
from commercial_app.core.responses import fail, ok
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from commercial_app.infrastructure.persistence.repositories.postgres_sla_policy_repository import (
    PostgresSlaPolicyRepository,
    SlaPolicyConflictError,
    SlaPolicyValidationError,
)
from commercial_app.interface.http.schemas.sla_policy_schemas import (
    CreateSlaPolicyBody,
    UpdateSlaPolicyBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


def _repo() -> PostgresSlaPolicyRepository:
    return PostgresSlaPolicyRepository()


@router.get("/sla-policies", operation_id="list_sla_policies")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def list_sla_policies(
    request: Request,
    include_inactive: bool = Query(default=False),
):
    if include_inactive and not has_manage(getattr(request.state, "user", None)):
        return fail(
            "Permissão insuficiente para listar políticas inativas.",
            403,
            operation_id="list_sla_policies",
        )
    try:
        items = _repo().list_policies(include_inactive=include_inactive)
        active_count = sum(1 for item in items if item.get("active"))
        return ok(
            {
                "items": items,
                "configured": active_count > 0,
                "includeInactive": include_inactive,
            },
            message="Políticas de SLA.",
            operation_id="list_sla_policies",
        )
    except PluginsRepositoryError:
        return ok(
            {"items": [], "configured": False, "includeInactive": include_inactive},
            message="Políticas de SLA.",
            operation_id="list_sla_policies",
        )


@router.post("/sla-policies", operation_id="create_sla_policy")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def create_sla_policy(
    _request: Request,
    body: CreateSlaPolicyBody = Body(...),
):
    try:
        created = _repo().create(
            code=body.code,
            name=body.name,
            applies_to=body.appliesTo,
            duration_hours=body.durationHours,
            calendar_code=body.calendarCode,
            active=body.active,
        )
        return ok(
            created,
            message="Política de SLA criada.",
            operation_id="create_sla_policy",
            status_code=201,
        )
    except SlaPolicyValidationError as exc:
        return fail(str(exc), 422, operation_id="create_sla_policy")
    except SlaPolicyConflictError as exc:
        return fail(str(exc), 409, operation_id="create_sla_policy")
    except PluginsRepositoryError:
        logger.exception("create_sla_policy_failed")
        return fail(
            "Erro ao criar política de SLA.",
            500,
            operation_id="create_sla_policy",
        )


@router.patch("/sla-policies/{policy_id}", operation_id="update_sla_policy")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def update_sla_policy(
    _request: Request,
    policy_id: str = Path(..., min_length=1),
    body: UpdateSlaPolicyBody = Body(...),
):
    try:
        fields = body.model_dump(exclude_unset=True)
        updated = _repo().update(
            policy_id,
            code=fields.get("code"),
            name=fields.get("name"),
            applies_to=fields.get("appliesTo"),
            duration_hours=fields.get("durationHours"),
            calendar_code=fields["calendarCode"]
            if "calendarCode" in fields
            else ...,
            active=fields.get("active"),
        )
        if updated is None:
            return fail(
                "Política de SLA não encontrada.",
                404,
                operation_id="update_sla_policy",
            )
        return ok(
            updated,
            message="Política de SLA atualizada.",
            operation_id="update_sla_policy",
        )
    except SlaPolicyValidationError as exc:
        return fail(str(exc), 422, operation_id="update_sla_policy")
    except SlaPolicyConflictError as exc:
        return fail(str(exc), 409, operation_id="update_sla_policy")
    except PluginsRepositoryError:
        logger.exception("update_sla_policy_failed")
        return fail(
            "Erro ao atualizar política de SLA.",
            500,
            operation_id="update_sla_policy",
        )


@router.delete("/sla-policies/{policy_id}", operation_id="deactivate_sla_policy")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def deactivate_sla_policy(
    _request: Request,
    policy_id: str = Path(..., min_length=1),
):
    try:
        deactivated = _repo().deactivate(policy_id)
        if deactivated is None:
            return fail(
                "Política de SLA não encontrada.",
                404,
                operation_id="deactivate_sla_policy",
            )
        return ok(
            deactivated,
            message="Política de SLA desativada.",
            operation_id="deactivate_sla_policy",
        )
    except SlaPolicyValidationError as exc:
        return fail(str(exc), 422, operation_id="deactivate_sla_policy")
    except PluginsRepositoryError:
        logger.exception("deactivate_sla_policy_failed")
        return fail(
            "Erro ao desativar política de SLA.",
            500,
            operation_id="deactivate_sla_policy",
        )
