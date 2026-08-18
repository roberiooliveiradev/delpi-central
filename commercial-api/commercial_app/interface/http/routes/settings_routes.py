"""GET /settings/sla-policies — empty until homologated."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_READ_PERMISSIONS,
)
from commercial_app.core.responses import fail, ok
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from commercial_app.infrastructure.persistence.repositories.postgres_sla_policy_repository import (
    PostgresSlaPolicyRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/sla-policies", operation_id="list_sla_policies")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def list_sla_policies(request: Request):
    try:
        items = PostgresSlaPolicyRepository().list_active()
        return ok(
            {"items": items, "configured": len(items) > 0},
            message="Políticas de SLA.",
            operation_id="list_sla_policies",
        )
    except PluginsRepositoryError:
        return ok(
            {"items": [], "configured": False},
            message="Políticas de SLA.",
            operation_id="list_sla_policies",
        )
