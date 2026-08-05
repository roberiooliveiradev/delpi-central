"""Guard: mutação de linhas conforme status do plano de Pessoal (Fase 3C.1)."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.planejamento_orcamentario.exceptions import (
    PersonnelPlanLockedError,
    PersonnelPlanNotFoundError,
)
from app.domain.services.planejamento_orcamentario.personnel_budget_constants import (
    EDITABLE_PLAN_STATUSES,
)


class PersonnelPlanLookup(Protocol):
    def get_personnel_plan(self, plan_id: str) -> dict[str, Any] | None: ...


def assert_personnel_plan_allows_mutation(
    repository: PersonnelPlanLookup,
    *,
    plan_id: str,
) -> dict[str, Any]:
    """Bloqueia se status ∉ {draft, changes_requested}."""
    plan = repository.get_personnel_plan(plan_id)
    if plan is None:
        raise PersonnelPlanNotFoundError("Planejamento de Pessoal não encontrado.")
    status = str(plan.get("status") or "")
    if status not in EDITABLE_PLAN_STATUSES:
        raise PersonnelPlanLockedError(
            f"Planejamento de Pessoal em status '{status}' está bloqueado para edição."
        )
    return plan
