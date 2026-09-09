"""Cobertura determinística de goals — autoridade de completude, não critic LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep


@dataclass(frozen=True)
class GoalCoverageResult:
    goal_id: str
    status: str
    step_ids: tuple[str, ...]
    evidence_ok: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "goalId": self.goal_id,
            "status": self.status,
            "stepIds": list(self.step_ids),
            "evidenceOk": self.evidence_ok,
        }


@dataclass(frozen=True)
class GoalCoverageReport:
    results: tuple[GoalCoverageResult, ...]
    complete: bool
    pending_goal_ids: tuple[str, ...]
    failed_goal_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "pendingGoalIds": list(self.pending_goal_ids),
            "failedGoalIds": list(self.failed_goal_ids),
            "results": [item.as_dict() for item in self.results],
        }


class ChatGoalCoverageService:
    @classmethod
    def evaluate(
        cls,
        plan: ActionPlan,
        *,
        execution_results: list[dict[str, Any]] | None = None,
    ) -> GoalCoverageReport:
        steps = plan.steps
        goals = plan.goals or cls._goals_from_steps(steps)
        by_goal: dict[str, list[ActionPlanStep]] = {}
        for step in steps:
            ids = step.goal_ids or ((f"g{len(by_goal) + 1}",) if not goals else ())
            if not ids and goals:
                # Unlabeled steps cover remaining pending goals in order.
                continue
            for goal_id in ids or ():
                by_goal.setdefault(goal_id, []).append(step)

        if goals and not any(step.goal_ids for step in steps):
            for index, goal in enumerate(goals):
                if index < len(steps):
                    by_goal.setdefault(goal.goal_id, []).append(steps[index])

        ok_by_action = cls._success_by_action_id(execution_results)
        results: list[GoalCoverageResult] = []
        pending: list[str] = []
        failed: list[str] = []
        for goal in goals:
            linked = by_goal.get(goal.goal_id) or []
            step_ids = tuple(step.step_id or step.action_id for step in linked)
            if not linked:
                results.append(
                    GoalCoverageResult(
                        goal_id=goal.goal_id,
                        status="pending",
                        step_ids=(),
                        evidence_ok=False,
                    )
                )
                pending.append(goal.goal_id)
                continue
            if execution_results is None:
                results.append(
                    GoalCoverageResult(
                        goal_id=goal.goal_id,
                        status="planned",
                        step_ids=step_ids,
                        evidence_ok=False,
                    )
                )
                continue
            evidence_ok = any(
                ok_by_action.get(step.action_id) is True for step in linked
            )
            failed_step = any(
                ok_by_action.get(step.action_id) is False for step in linked
            )
            if evidence_ok:
                status = "fulfilled"
            elif failed_step:
                status = "failed"
                failed.append(goal.goal_id)
            else:
                status = "pending"
                pending.append(goal.goal_id)
            results.append(
                GoalCoverageResult(
                    goal_id=goal.goal_id,
                    status=status,
                    step_ids=step_ids,
                    evidence_ok=evidence_ok,
                )
            )

        complete = bool(goals) and not pending and not failed
        if not goals:
            complete = bool(steps)
        return GoalCoverageReport(
            results=tuple(results),
            complete=complete,
            pending_goal_ids=tuple(pending),
            failed_goal_ids=tuple(failed),
        )

    @classmethod
    def _goals_from_steps(cls, steps: tuple[ActionPlanStep, ...]) -> tuple[ActionPlanGoal, ...]:
        if len(steps) <= 1:
            if not steps:
                return ()
            return (
                ActionPlanGoal(goal_id="g1", intent=steps[0].action_id, status="pending"),
            )
        return tuple(
            ActionPlanGoal(
                goal_id=f"g{index + 1}",
                intent=step.action_id,
                status="pending",
            )
            for index, step in enumerate(steps)
        )

    @classmethod
    def _success_by_action_id(
        cls,
        execution_results: list[dict[str, Any]] | None,
    ) -> dict[str, bool]:
        mapping: dict[str, bool] = {}
        for item in execution_results or []:
            if not isinstance(item, dict):
                continue
            action_id = str(
                item.get("actionId")
                or (item.get("arguments") or {}).get("actionId")
                or (item.get("metadata") or {}).get("actionId")
                or ""
            ).strip()
            if not action_id:
                continue
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            ok = item.get("ok")
            if ok is None:
                ok = meta.get("ok")
            mapping[action_id] = bool(ok)
        return mapping
