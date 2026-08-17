from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_team_roster import ManageTeamRosterUseCase
from commercial_app.composition.commercial_composer import build_manage_team_roster_use_case
from commercial_app.core.responses import fail, ok
from commercial_app.domain.services.team_roster_messages_content_service import (
    TeamRosterMessagesContentService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/administration", tags=["Commercial administration"])


def _use_case() -> ManageTeamRosterUseCase:
    return build_manage_team_roster_use_case()


@router.get("/team-roster", operation_id="list_commercial_team_roster")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_team_roster(
    _request: Request,
    group_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    try:
        items = _use_case().list_roster(
            group_id=group_id,
            portfolio_id=portfolio_id,
            q=q,
        )
        return ok(
            {"items": items},
            message=TeamRosterMessagesContentService.message("listOk"),
            operation_id="list_commercial_team_roster",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="list_commercial_team_roster")
    except Exception:
        logger.exception("list_commercial_team_roster_failed")
        return fail(
            "Erro interno ao carregar a equipe.",
            500,
            operation_id="list_commercial_team_roster",
        )
