from __future__ import annotations

from delpi_auth.authorization import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    PLANEJAMENTO_ORCAMENTARIO_ACCESS,
    PLANEJAMENTO_ORCAMENTARIO_ADMIN,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_EXPORT,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_SUBMIT,
    PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE,
    PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_SUBMIT,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW,
    PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.exceptions import BudgetPlanningError
from app.core.responses import error_response, not_found_response


def build_actor() -> BudgetActor:
    user = get_current_user()
    if user is None:
        return BudgetActor(user_id="unknown", user_name="Usuário", permissions=frozenset())
    user_id = str(getattr(user, "id", "") or "unknown")
    raw_name = getattr(user, "name", None) or getattr(user, "email", None) or "Usuário"
    perms = set()
    for code in (
        PLANEJAMENTO_ORCAMENTARIO_ACCESS,
        PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW,
        PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE,
        PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE,
        PLANEJAMENTO_ORCAMENTARIO_ADMIN,
        PLANEJAMENTO_ORCAMENTARIO_CAPEX_SUBMIT,
        PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE,
        PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW,
        PLANEJAMENTO_ORCAMENTARIO_CAPEX_EXPORT,
        PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW,
        PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT,
        PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_SUBMIT,
        PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE,
    ):
        if has_permission(user, code):
            perms.add(code)
    return BudgetActor(user_id=user_id, user_name=str(raw_name), permissions=frozenset(perms))


def handle_budget_error(exc: BudgetPlanningError):
    details = getattr(exc, "details", None)
    meta = details if isinstance(details, dict) else None
    if exc.status_code == 404:
        return not_found_response(str(exc), code=exc.code)
    return error_response(
        str(exc),
        status_code=exc.status_code,
        code=exc.code,
        recoverable=exc.status_code in {400, 409, 422},
        meta=meta,
    )
