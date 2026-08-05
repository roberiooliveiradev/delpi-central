"""Guard: mutação de investimentos/anexos conforme status do plano CAPEX."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.planejamento_orcamentario.capex_plan_constants import (
    EDITABLE_PLAN_STATUSES,
)
from app.domain.services.planejamento_orcamentario.exceptions import CapexPlanLockedError


class CapexPlanLookup(Protocol):
    def get_capex_plan_by_exercise_cc(
        self,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any] | None: ...


def assert_plan_allows_mutation(
    repository: CapexPlanLookup,
    *,
    exercise_id: str,
    cost_center_id: str,
    unit_id: str | None = None,
) -> dict[str, Any] | None:
    """Plano inexistente ≡ draft. Bloqueia se status ∉ {draft, changes_requested}."""
    plan = repository.get_capex_plan_by_exercise_cc(
        exercise_id=exercise_id,
        cost_center_id=cost_center_id,
        unit_id=unit_id,
    )
    if plan is None:
        return None
    status = str(plan.get("status") or "")
    if status not in EDITABLE_PLAN_STATUSES:
        raise CapexPlanLockedError(
            f"Planejamento CAPEX em status '{status}' está bloqueado para edição."
        )
    return plan
