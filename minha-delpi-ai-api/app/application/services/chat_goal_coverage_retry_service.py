"""Planner-driven enrichment pós-execute via Goal Coverage (E5.S4).

Propõe action adicional somente entre allowed candidates quando há goal
não coberto (mismatch/pending). Não amplia permissions; não faz fan-out
por entity/scope map. Dedupa actionId já tentado e respeita budget.
"""

from __future__ import annotations

from typing import Any

from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.chat_goal_coverage_service import (
    ChatGoalCoverageService,
    GoalCoverageReport,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)
from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)

# Outcomes que justificam enrichment adicional (não covered / não resolvível só com o resultado atual).
_UNCOVERED_STATUSES = frozenset({"mismatch", "pending"})


class ChatGoalCoverageRetryService:
    @classmethod
    def plan_follow_ups(
        cls,
        *,
        message: str,
        tool_calls: list[dict[str, Any]] | None,
        remaining_slots: int,
        allowed_action_ids: list[str] | None,
        actions_by_id: dict[str, dict[str, Any]] | None = None,
        retriever=None,
    ) -> list[dict[str, Any]]:
        if remaining_slots < 1:
            return []
        allowed = [
            str(item).strip()
            for item in (allowed_action_ids or [])
            if str(item).strip()
        ]
        if not allowed:
            return []
        calls = [item for item in (tool_calls or []) if isinstance(item, dict)]
        tried = cls._tried_action_ids(calls)
        catalog = dict(actions_by_id or {})
        plan = cls._plan_from_tool_calls(calls, message=message)
        if plan is None:
            return []
        report = ChatGoalCoverageService.evaluate(
            plan,
            execution_results=calls,
            message=message,
            actions_by_id=catalog,
        )
        uncovered = cls._uncovered_goal_ids(report)
        if not uncovered:
            return []
        if report.complete:
            return []
        budget = cls._retry_budget(remaining_slots)
        if budget < 1:
            return []
        query = cls._search_query(report, plan, message, uncovered=uncovered)
        remaining_allowed = [item for item in allowed if item not in tried]
        if not remaining_allowed:
            return []
        candidates = cls._retrieve_candidates(
            query,
            remaining_allowed=remaining_allowed,
            catalog=catalog,
            retriever=retriever,
        )
        justification = cls._justification(report, uncovered=uncovered, query=query)
        parameters = cls._parameters_from_previous(calls)
        follow_ups: list[dict[str, Any]] = []
        seen: set[str] = set(tried)
        for action in candidates:
            action_id = str(action.get("actionId") or action.get("action_id") or "").strip()
            if not action_id or action_id in seen:
                continue
            if action_id not in remaining_allowed:
                continue
            follow_ups.append(
                cls._to_tool_call(
                    action,
                    parameters=parameters,
                    query=query,
                    justification=justification,
                )
            )
            seen.add(action_id)
            if len(follow_ups) >= budget:
                break
        return follow_ups

    @classmethod
    def _uncovered_goal_ids(cls, report: GoalCoverageReport) -> tuple[str, ...]:
        wanted: list[str] = []
        for result in report.results:
            if result.status in _UNCOVERED_STATUSES and result.goal_id not in wanted:
                wanted.append(result.goal_id)
        for goal_id in list(report.mismatch_goal_ids) + list(report.pending_goal_ids):
            if goal_id and goal_id not in wanted:
                wanted.append(goal_id)
        return tuple(wanted)

    @classmethod
    def _retry_budget(cls, remaining_slots: int) -> int:
        cap = OpenApiToolRoutingContentService.int_setting(
            "goalCoverage",
            "maxRetryActionsPerTurn",
            default=2,
        )
        cap = max(0, int(cap))
        return max(0, min(int(remaining_slots), cap if cap > 0 else int(remaining_slots)))

    @classmethod
    def _justification(
        cls,
        report: GoalCoverageReport,
        *,
        uncovered: tuple[str, ...],
        query: str,
    ) -> dict[str, Any]:
        statuses = {
            result.goal_id: result.status
            for result in report.results
            if result.goal_id in uncovered
        }
        return {
            "enrichmentReason": "goal_coverage_gap",
            "uncoveredGoalIds": list(uncovered),
            "uncoveredStatuses": statuses,
            "coverageQuery": query,
        }

    @classmethod
    def _plan_from_tool_calls(
        cls,
        calls: list[dict[str, Any]],
        *,
        message: str,
    ) -> ActionPlan | None:
        steps: list[ActionPlanStep] = []
        for index, item in enumerate(calls):
            name = str(item.get("name") or "")
            if name and name != "execute_external_action":
                continue
            action_id = cls._action_id_of(item)
            if not action_id:
                continue
            arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            steps.append(
                ActionPlanStep(
                    action_id=action_id,
                    goal_ids=("g1",),
                    step_id=f"s{index + 1}",
                    arguments=dict(arguments),
                )
            )
        if not steps:
            return None
        return ActionPlan(
            goals=(ActionPlanGoal(goal_id="g1", intent=str(message or "")[:160]),),
            steps=tuple(steps),
        )

    @classmethod
    def _search_query(
        cls,
        report: GoalCoverageReport,
        plan: ActionPlan,
        message: str,
        *,
        uncovered: tuple[str, ...],
    ) -> str:
        wanted = set(uncovered)
        for goal in plan.goals:
            if goal.goal_id in wanted and str(goal.intent or "").strip():
                return str(goal.intent).strip()
        return str(message or "").strip()

    @classmethod
    def _retrieve_candidates(
        cls,
        query: str,
        *,
        remaining_allowed: list[str],
        catalog: dict[str, dict[str, Any]],
        retriever,
    ) -> list[dict[str, Any]]:
        remaining_set = set(remaining_allowed)
        raws: list[dict[str, Any]] = []
        if retriever is not None:
            retrieved = retriever.retrieve(
                query,
                allowed_action_ids=remaining_allowed,
                catalog_actions=list(catalog.values()),
            )
            for item in retrieved or []:
                raw = item.raw_action if hasattr(item, "raw_action") else item
                if isinstance(raw, dict):
                    raws.append(raw)
        if not raws:
            raws = [
                catalog[action_id]
                for action_id in remaining_allowed
                if isinstance(catalog.get(action_id), dict)
            ]
        raws = [
            item
            for item in raws
            if str(item.get("actionId") or item.get("action_id") or "").strip() in remaining_set
        ]
        raws = OpenApiWhenNotToUseGuidanceService.filter_candidates(
            query,
            raws,
            raw_action_of=lambda item: item,
        )
        raws = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
            query,
            raws,
            raw_action_of=lambda item: item,
        )
        return raws

    @classmethod
    def _tried_action_ids(cls, calls: list[dict[str, Any]]) -> set[str]:
        return {cls._action_id_of(item) for item in calls if cls._action_id_of(item)}

    @classmethod
    def _action_id_of(cls, item: dict[str, Any]) -> str:
        arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        return str(
            item.get("actionId")
            or arguments.get("actionId")
            or arguments.get("action_id")
            or metadata.get("actionId")
            or ""
        ).strip()

    @classmethod
    def _parameters_from_previous(cls, calls: list[dict[str, Any]]) -> dict[str, Any]:
        for item in calls:
            arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
            parameters = arguments.get("parameters")
            if isinstance(parameters, dict) and parameters:
                return dict(parameters)
        return {}

    @classmethod
    def _to_tool_call(
        cls,
        action: dict[str, Any],
        *,
        parameters: dict[str, Any],
        query: str,
        justification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        action_id = str(action.get("actionId") or action.get("action_id") or "").strip()
        reason = OpenApiToolRoutingContentService.get(
            "selectionReasons",
            "openapiFirstPlan",
        )
        meta: dict[str, Any] = {
            "selectionMode": "openapi_first",
            "goalCoverageRetry": True,
            "compositionRole": "coverage_retry",
            "actionId": action_id,
            "providerKey": action.get("providerKey"),
            "operationId": action.get("operationId") or action.get("operation_id"),
            "path": action.get("path"),
            "method": action.get("method"),
            "coverageQuery": query,
        }
        if isinstance(justification, dict):
            meta.update(justification)
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": action_id,
                "parameters": dict(parameters),
            },
            "reason": reason,
            "metadata": meta,
        }
