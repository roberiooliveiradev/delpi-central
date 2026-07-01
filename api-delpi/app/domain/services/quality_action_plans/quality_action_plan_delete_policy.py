from __future__ import annotations

from typing import Any


def _assert_plan_governance_blocks_mutation(
    plan: dict[str, Any],
    *,
    was_ever_completed: bool,
    verb: str,
) -> None:
    status = plan.get("status")
    approval_status = plan.get("effectiveness_approval_status")

    if status == "completed" or was_ever_completed:
        raise ValueError(
            f"Não é possível {verb} plano que já foi concluído, mesmo após reabertura."
        )
    if approval_status == "approved":
        raise ValueError(f"Não é possível {verb} plano com eficácia aprovada.")
    if approval_status == "pending_review":
        raise ValueError(f"Não é possível {verb} plano com eficácia pendente de aprovação.")


def assert_plan_deletable(
    plan: dict[str, Any],
    *,
    was_ever_completed: bool = False,
) -> None:
    _assert_plan_governance_blocks_mutation(
        plan,
        was_ever_completed=was_ever_completed,
        verb="excluir",
    )


def assert_plan_revision_restorable(
    plan: dict[str, Any],
    *,
    was_ever_completed: bool = False,
) -> None:
    _assert_plan_governance_blocks_mutation(
        plan,
        was_ever_completed=was_ever_completed,
        verb="restaurar revisão de",
    )
