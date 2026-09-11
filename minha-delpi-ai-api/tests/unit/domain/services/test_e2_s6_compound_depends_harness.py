"""E2.S6 — pedidos compostos: dependsOn / parallelGroup a partir do TU (harness)."""

from __future__ import annotations

from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService


def test_compound_request_splits_goals_and_preserves_order() -> None:
    message = (
        "1. estoque do produto 10080001\n"
        "2. fornecedores desse produto\n"
        "3. resume os achados"
    )
    understanding = ChatTurnUnderstandingService.analyze(message)
    assert understanding.subtask_count >= 2

    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message=message,
        response_mode="normal",
        action_catalog=[],
        allowed_action_ids=[],
    )
    assert len(plan.tasks) >= 2
    # Ordem de goals preservada no plano.
    assert plan.tasks[0].id == "t-1"
    assert plan.tasks[1].id == "t-2"


def test_compound_dependent_reference_gets_depends_on() -> None:
    """Sibling: segundo goal referencia entidade do primeiro → dependsOn."""
    message = (
        "1. estoque do produto 10080001\n"
        "2. estrutura desse produto"
    )
    understanding = ChatTurnUnderstandingService.analyze(message)
    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message=message,
        response_mode="normal",
        action_catalog=[],
        allowed_action_ids=[],
    )
    dependent = [task for task in plan.tasks if task.depends_on]
    assert dependent, "expected at least one dependent task via prior-code heuristic"
    for task in dependent:
        for dep in task.depends_on:
            assert dep.startswith("t-") or dep.startswith("st-")


def test_compound_negative_single_goal_no_spurious_depends() -> None:
    understanding = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message="qual o estoque do produto 10080001?",
        response_mode="normal",
        action_catalog=[],
        allowed_action_ids=[],
    )
    assert len(plan.tasks) == 1
    assert plan.tasks[0].depends_on == ()
