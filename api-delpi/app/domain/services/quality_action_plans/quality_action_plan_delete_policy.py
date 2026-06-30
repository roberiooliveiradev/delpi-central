from __future__ import annotations

from typing import Any


def assert_plan_deletable(plan: dict[str, Any]) -> None:
    status = plan.get("status")
    approval_status = plan.get("effectiveness_approval_status")

    if status == "completed":
        raise ValueError("Não é possível excluir plano concluído.")
    if approval_status == "approved":
        raise ValueError("Não é possível excluir plano com eficácia aprovada.")
    if approval_status == "pending_review":
        raise ValueError("Não é possível excluir plano com eficácia pendente de aprovação.")
