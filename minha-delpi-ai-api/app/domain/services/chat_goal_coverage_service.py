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

# Outcome canônico (E5.S3) + estados intermediários de planejamento.
_COVERAGE_OUTCOMES = frozenset(
    {
        "pending",
        "planned",
        "fulfilled",
        "partial",
        "blocked",
        "needs_more_data",
        "failed",
        "mismatch",
    }
)


@dataclass(frozen=True)
class GoalCoverageResult:
    goal_id: str
    status: str
    step_ids: tuple[str, ...]
    evidence_ok: bool

    def as_dict(self) -> dict[str, Any]:
        status = self.status if self.status in _COVERAGE_OUTCOMES else "pending"
        return {
            "goalId": self.goal_id,
            "status": status,
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
    partial_goal_ids: tuple[str, ...] = ()
    blocked_goal_ids: tuple[str, ...] = ()
    needs_more_data_goal_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "pendingGoalIds": list(self.pending_goal_ids),
            "failedGoalIds": list(self.failed_goal_ids),
            "mismatchGoalIds": list(self.mismatch_goal_ids),
            "partialGoalIds": list(self.partial_goal_ids),
            "blockedGoalIds": list(self.blocked_goal_ids),
            "needsMoreDataGoalIds": list(self.needs_more_data_goal_ids),
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
        partial: list[str] = []
        blocked: list[str] = []
        needs_more: list[str] = []
        for goal in goals:
            linked = by_goal.get(goal.goal_id) or []
            step_ids = tuple(step.step_id or step.action_id for step in linked)
            if str(goal.status or "").strip().lower() == "blocked":
                results.append(
                    GoalCoverageResult(
                        goal_id=goal.goal_id,
                        status="blocked",
                        step_ids=step_ids,
                        evidence_ok=False,
                    )
                )
                blocked.append(goal.goal_id)
                continue
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
            if cls._blocked_execution(linked, results_by_action):
                results.append(
                    GoalCoverageResult(
                        goal_id=goal.goal_id,
                        status="blocked",
                        step_ids=step_ids,
                        evidence_ok=False,
                    )
                )
                blocked.append(goal.goal_id)
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
            partial_ok = evidence_ok and not empty_ok and cls._partial_result_coverage(
                linked,
                results_by_action,
            )
            if capability_mismatch:
                status = "mismatch"
                mismatch.append(goal.goal_id)
                evidence_ok = False
            elif empty_ok:
                status = "needs_more_data"
                needs_more.append(goal.goal_id)
                evidence_ok = False
            elif partial_ok:
                status = "partial"
                partial.append(goal.goal_id)
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

        incomplete = pending or failed or mismatch or partial or blocked or needs_more
        complete = bool(goals) and not incomplete
        if not goals:
            complete = bool(steps)
        return GoalCoverageReport(
            results=tuple(results),
            complete=complete,
            pending_goal_ids=tuple(pending),
            failed_goal_ids=tuple(failed),
            mismatch_goal_ids=tuple(mismatch),
            partial_goal_ids=tuple(partial),
            blocked_goal_ids=tuple(blocked),
            needs_more_data_goal_ids=tuple(needs_more),
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
    def _blocked_execution(
        cls,
        linked: list[ActionPlanStep],
        results_by_action: dict[str, dict[str, Any]],
    ) -> bool:
        for step in linked:
            item = results_by_action.get(step.action_id)
            if not isinstance(item, dict):
                continue
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            status_code = item.get("statusCode")
            if status_code is None:
                status_code = meta.get("statusCode")
            try:
                code = int(status_code) if status_code is not None else None
            except (TypeError, ValueError):
                code = None
            if code in {401, 403}:
                return True
            reason = str(
                item.get("blockReason")
                or meta.get("blockReason")
                or item.get("blockedReason")
                or meta.get("blockedReason")
                or ""
            ).strip()
            if reason:
                return True
            if item.get("blocked") is True or meta.get("blocked") is True:
                return True
        return False

    @classmethod
    def _partial_result_coverage(
        cls,
        linked: list[ActionPlanStep],
        results_by_action: dict[str, dict[str, Any]],
    ) -> bool:
        if not OpenApiToolRoutingContentService.bool_setting(
            "goalCoverage",
            "partialPaginationEnabled",
            default=True,
        ):
            return False
        return any(
            cls._looks_partial_result(results_by_action[step.action_id])
            for step in linked
            if step.action_id in results_by_action
            and cls._http_ok(results_by_action[step.action_id])
        )

    @classmethod
    def _looks_partial_result(cls, item: dict[str, Any]) -> bool:
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        notice = meta.get("dataCoverageNotice") or item.get("dataCoverageNotice")
        if isinstance(notice, dict) and str(notice.get("kind") or "").strip().lower() in {
            "partial",
            "truncated",
            "paginated",
        }:
            return True
        if meta.get("truncated") is True or item.get("truncated") is True:
            return True
        if meta.get("hasMore") is True or item.get("hasMore") is True:
            return True
        root = cls._unwrap_data(item.get("data"))
        if not isinstance(root, dict):
            return False
        if root.get("hasMore") is True or root.get("truncated") is True:
            return True
        pagination = root.get("pagination")
        if isinstance(pagination, dict):
            if pagination.get("hasMore") is True or pagination.get("truncated") is True:
                return True
            page = cls._as_int(pagination.get("page"))
            total_pages = cls._as_int(pagination.get("totalPages") or pagination.get("total_pages"))
            if page is not None and total_pages is not None and total_pages > page:
                return True
        items = root.get("items")
        if not isinstance(items, list):
            return False
        shown = len(items)
        total = cls._as_int(root.get("total"))
        page = cls._as_int(root.get("page"))
        total_pages = cls._as_int(root.get("total_pages") or root.get("totalPages"))
        if total is not None and total > shown:
            return True
        if page is not None and total_pages is not None and total_pages > page:
            return True
        return False

    @classmethod
    def _unwrap_data(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        nested = data.get("data")
        if isinstance(nested, dict) and (
            "items" in nested or "pagination" in nested or "total" in nested
        ):
            return nested
        return data

    @classmethod
    def _as_int(cls, value: Any) -> int | None:
        try:
            if value is None or value is False:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

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
