"""Cobertura determinística de goals — autoridade de completude, não critic LLM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)
from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)


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
    mismatch_goal_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "pendingGoalIds": list(self.pending_goal_ids),
            "failedGoalIds": list(self.failed_goal_ids),
            "mismatchGoalIds": list(self.mismatch_goal_ids),
            "results": [item.as_dict() for item in self.results],
        }


class ChatGoalCoverageService:
    @classmethod
    def evaluate(
        cls,
        plan: ActionPlan,
        *,
        execution_results: list[dict[str, Any]] | None = None,
        message: str | None = None,
        actions_by_id: dict[str, dict[str, Any]] | None = None,
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
        results_by_action = cls._results_by_action_id(execution_results)
        results: list[GoalCoverageResult] = []
        pending: list[str] = []
        failed: list[str] = []
        mismatch: list[str] = []
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
            empty_ok = evidence_ok and cls._empty_payload_not_fulfilled(
                linked,
                results_by_action,
            )
            capability_mismatch = evidence_ok and cls._capability_mismatch(
                message=message,
                linked=linked,
                actions_by_id=actions_by_id,
            )
            if capability_mismatch:
                status = "mismatch"
                mismatch.append(goal.goal_id)
                evidence_ok = False
            elif empty_ok:
                status = "failed"
                failed.append(goal.goal_id)
                evidence_ok = False
            elif evidence_ok:
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

        complete = bool(goals) and not pending and not failed and not mismatch
        if not goals:
            complete = bool(steps)
        return GoalCoverageReport(
            results=tuple(results),
            complete=complete,
            pending_goal_ids=tuple(pending),
            failed_goal_ids=tuple(failed),
            mismatch_goal_ids=tuple(mismatch),
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
            action_id = cls._action_id_of(item)
            if not action_id:
                continue
            mapping[action_id] = cls._http_ok(item)
        return mapping

    @classmethod
    def _results_by_action_id(
        cls,
        execution_results: list[dict[str, Any]] | None,
    ) -> dict[str, dict[str, Any]]:
        mapping: dict[str, dict[str, Any]] = {}
        for item in execution_results or []:
            action_id = cls._action_id_of(item)
            if action_id:
                mapping[action_id] = item
        return mapping

    @classmethod
    def _action_id_of(cls, item: Any) -> str:
        if not isinstance(item, dict):
            return ""
        return str(
            item.get("actionId")
            or (item.get("arguments") or {}).get("actionId")
            or (item.get("metadata") or {}).get("actionId")
            or ""
        ).strip()

    @classmethod
    def _http_ok(cls, item: dict[str, Any]) -> bool:
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        ok = item.get("ok")
        if ok is None:
            ok = meta.get("ok")
        return bool(ok)

    @classmethod
    def _empty_payload_not_fulfilled(
        cls,
        linked: list[ActionPlanStep],
        results_by_action: dict[str, dict[str, Any]],
    ) -> bool:
        if not OpenApiToolRoutingContentService.bool_setting(
            "goalCoverage",
            "emptyPayloadNotFulfilled",
            default=True,
        ):
            return False
        ok_items = [
            results_by_action[step.action_id]
            for step in linked
            if step.action_id in results_by_action
            and cls._http_ok(results_by_action[step.action_id])
        ]
        if not ok_items:
            return False
        return all(cls._is_empty_payload(item) for item in ok_items)

    @classmethod
    def _is_empty_payload(cls, item: dict[str, Any]) -> bool:
        data = item.get("data")
        if data is None:
            return False
        if isinstance(data, list):
            return len(data) == 0
        if not isinstance(data, dict):
            return False
        if not data:
            return True
        for key in ("items", "rows", "records"):
            value = data.get(key)
            if isinstance(value, list) and len(value) == 0:
                return True
        nested = data.get("data")
        if isinstance(nested, dict):
            items = nested.get("items")
            if isinstance(items, list) and len(items) == 0:
                return True
        return False

    @classmethod
    def _capability_mismatch(
        cls,
        *,
        message: str | None,
        linked: list[ActionPlanStep],
        actions_by_id: dict[str, dict[str, Any]] | None,
    ) -> bool:
        if not str(message or "").strip() or not actions_by_id:
            return False
        executed = [
            actions_by_id.get(step.action_id)
            for step in linked
            if isinstance(actions_by_id.get(step.action_id), dict)
        ]
        if not executed:
            return False
        if OpenApiToolRoutingContentService.bool_setting(
            "goalCoverage",
            "mismatchOnWhenNotToUse",
            default=True,
        ) and any(
            OpenApiWhenNotToUseGuidanceService.matches_message(message, action)
            for action in executed
        ):
            return True
        if not OpenApiToolRoutingContentService.bool_setting(
            "goalCoverage",
            "requireWhenToUseMatchWhenQuotesExist",
            default=True,
        ):
            return False
        executed_ids = {step.action_id for step in linked}
        executed_matches = any(
            OpenApiWhenNotToUseGuidanceService.matches_positive(message, action)
            for action in executed
        )
        executed_has_quotes = any(
            OpenApiWhenNotToUseGuidanceService.quoted_positive_phrases(action)
            for action in executed
        )
        if executed_matches or not executed_has_quotes:
            return False
        return any(
            action_id not in executed_ids
            and OpenApiWhenNotToUseGuidanceService.matches_positive(message, action)
            for action_id, action in actions_by_id.items()
            if isinstance(action, dict)
        )
