"""Plano estruturado de execução de actions OpenAPI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_PLANNER_MODES = frozenset(
    {
        "DIRECT",
        "SEARCH_ACTIONS",
        "SEARCH_KNOWLEDGE",
        "SEARCH_MIXED",
        "EXECUTE",
        "CLARIFY",
        "COMPLETE",
    }
)
_SEARCH_REASONS = frozenset(
    {
        "candidate_insufficiency",
        "compound_goal",
        "ambiguous_retrieval",
        "knowledge_reformulation",
    }
)
_GOAL_STATUSES = frozenset({"pending", "planned", "fulfilled", "failed", "blocked"})


def _tuple_str(values: Any) -> tuple[str, ...]:
    if not isinstance(values, list | tuple):
        return ()
    return tuple(str(item).strip() for item in values if str(item or "").strip())


@dataclass(frozen=True)
class ActionPlanGoal:
    goal_id: str
    intent: str
    status: str = "pending"
    depends_on: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "goalId": self.goal_id,
            "intent": self.intent,
            "status": self.status if self.status in _GOAL_STATUSES else "pending",
        }
        if self.depends_on:
            payload["dependsOn"] = list(self.depends_on)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionPlanGoal | None:
        goal_id = str(payload.get("goalId") or payload.get("goal_id") or "").strip()
        intent = str(payload.get("intent") or "").strip()
        if not goal_id:
            return None
        status = str(payload.get("status") or "pending").strip().lower()
        if status not in _GOAL_STATUSES:
            status = "pending"
        return cls(
            goal_id=goal_id,
            intent=intent or goal_id,
            status=status,
            depends_on=_tuple_str(payload.get("dependsOn") or payload.get("depends_on")),
        )


@dataclass(frozen=True)
class ActionPlanSearchRequest:
    goal_id: str
    query: str
    reason: str = "compound_goal"

    def as_dict(self) -> dict[str, Any]:
        reason = self.reason if self.reason in _SEARCH_REASONS else "compound_goal"
        return {"goalId": self.goal_id, "query": self.query, "reason": reason}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionPlanSearchRequest | None:
        query = str(payload.get("query") or "").strip()
        if not query:
            return None
        reason = str(payload.get("reason") or "compound_goal").strip()
        if reason not in _SEARCH_REASONS:
            reason = "compound_goal"
        return cls(
            goal_id=str(payload.get("goalId") or payload.get("goal_id") or "").strip(),
            query=query,
            reason=reason,
        )


@dataclass(frozen=True)
class ActionPlanStep:
    action_id: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    confidence: float | None = None
    step_id: str = ""
    goal_ids: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "actionId": self.action_id,
            "arguments": dict(self.arguments or {}),
            "reason": self.reason,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.step_id:
            payload["stepId"] = self.step_id
        if self.goal_ids:
            payload["goalIds"] = list(self.goal_ids)
        if self.depends_on:
            payload["dependsOn"] = list(self.depends_on)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ActionPlanStep:
        arguments = payload.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {}
        confidence_raw = payload.get("confidence")
        confidence: float | None
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else None
        except (TypeError, ValueError):
            confidence = None
        return cls(
            action_id=str(payload.get("actionId") or payload.get("action_id") or "").strip(),
            arguments=dict(arguments),
            reason=str(payload.get("reason") or "").strip(),
            confidence=confidence,
            step_id=str(payload.get("stepId") or payload.get("step_id") or "").strip(),
            goal_ids=_tuple_str(payload.get("goalIds") or payload.get("goal_ids")),
            depends_on=_tuple_str(payload.get("dependsOn") or payload.get("depends_on")),
        )


@dataclass(frozen=True)
class ActionPlan:
    steps: tuple[ActionPlanStep, ...] = ()
    clarify: str | None = None
    selection_mode: str = "openapi_first"
    metadata: dict[str, Any] = field(default_factory=dict)
    plan_version: str = "1"
    mode: str = "EXECUTE"
    goals: tuple[ActionPlanGoal, ...] = ()
    candidate_set_id: str = ""
    requested_presentation: str | None = None
    clarification_kind: str | None = None
    search_action_requests: tuple[ActionPlanSearchRequest, ...] = ()
    search_knowledge_requests: tuple[ActionPlanSearchRequest, ...] = ()
    context_references: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "steps": [step.as_dict() for step in self.steps],
            "clarify": self.clarify,
            "selectionMode": self.selection_mode,
            "metadata": dict(self.metadata or {}),
            "planVersion": self.plan_version,
            "mode": self.mode,
        }
        if self.goals:
            payload["goals"] = [goal.as_dict() for goal in self.goals]
        if self.candidate_set_id:
            payload["candidateSetId"] = self.candidate_set_id
        if self.requested_presentation:
            payload["requestedPresentation"] = self.requested_presentation
        if self.clarification_kind:
            payload["clarificationKind"] = self.clarification_kind
        if self.search_action_requests or self.search_knowledge_requests:
            payload["searchRequests"] = {
                "actions": [item.as_dict() for item in self.search_action_requests],
                "knowledge": [item.as_dict() for item in self.search_knowledge_requests],
            }
        if self.context_references:
            payload["contextReferences"] = list(self.context_references)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> ActionPlan:
        if not isinstance(payload, dict):
            return cls()
        raw_steps = payload.get("steps") or []
        steps: list[ActionPlanStep] = []
        if isinstance(raw_steps, list):
            for item in raw_steps:
                if isinstance(item, dict):
                    step = ActionPlanStep.from_dict(item)
                    if step.action_id:
                        steps.append(step)
        clarify = payload.get("clarify")
        goals: list[ActionPlanGoal] = []
        for item in payload.get("goals") or []:
            if isinstance(item, dict):
                goal = ActionPlanGoal.from_dict(item)
                if goal is not None:
                    goals.append(goal)
        search = payload.get("searchRequests") if isinstance(payload.get("searchRequests"), dict) else {}
        action_reqs: list[ActionPlanSearchRequest] = []
        knowledge_reqs: list[ActionPlanSearchRequest] = []
        for item in (search.get("actions") if isinstance(search, dict) else None) or []:
            if isinstance(item, dict):
                parsed = ActionPlanSearchRequest.from_dict(item)
                if parsed is not None:
                    action_reqs.append(parsed)
        for item in (search.get("knowledge") if isinstance(search, dict) else None) or []:
            if isinstance(item, dict):
                parsed = ActionPlanSearchRequest.from_dict(item)
                if parsed is not None:
                    knowledge_reqs.append(parsed)
        mode = str(payload.get("mode") or "").strip().upper()
        if mode not in _PLANNER_MODES:
            if action_reqs or knowledge_reqs:
                mode = "SEARCH_MIXED" if action_reqs and knowledge_reqs else (
                    "SEARCH_KNOWLEDGE" if knowledge_reqs else "SEARCH_ACTIONS"
                )
            elif str(clarify or "").strip() and not steps:
                mode = "CLARIFY"
            elif steps:
                mode = "EXECUTE"
            else:
                mode = "DIRECT"
        presentation = str(
            payload.get("requestedPresentation") or payload.get("requested_presentation") or ""
        ).strip().lower() or None
        return cls(
            steps=tuple(steps),
            clarify=str(clarify).strip() if clarify else None,
            selection_mode=str(
                payload.get("selectionMode") or payload.get("selection_mode") or "openapi_first"
            ),
            metadata=(
                dict(payload.get("metadata"))
                if isinstance(payload.get("metadata"), dict)
                else {}
            ),
            plan_version=str(payload.get("planVersion") or payload.get("plan_version") or "1").strip()
            or "1",
            mode=mode,
            goals=tuple(goals),
            candidate_set_id=str(
                payload.get("candidateSetId") or payload.get("candidate_set_id") or ""
            ).strip(),
            requested_presentation=presentation,
            clarification_kind=str(
                payload.get("clarificationKind") or payload.get("clarification_kind") or ""
            ).strip()
            or None,
            search_action_requests=tuple(action_reqs),
            search_knowledge_requests=tuple(knowledge_reqs),
            context_references=_tuple_str(
                payload.get("contextReferences") or payload.get("context_references")
            ),
        )

    def with_updates(self, **changes: Any) -> ActionPlan:
        payload = self.as_dict()
        payload.update(changes)
        merged = ActionPlan.from_dict(payload)
        metadata = dict(self.metadata or {})
        extra_meta = changes.get("metadata")
        if isinstance(extra_meta, dict):
            metadata.update(extra_meta)
        return ActionPlan(
            steps=changes.get("steps", merged.steps) if "steps" in changes else merged.steps,
            clarify=changes["clarify"] if "clarify" in changes else merged.clarify,
            selection_mode=merged.selection_mode,
            metadata=metadata if extra_meta is not None or "metadata" in changes else dict(self.metadata or {}),
            plan_version=merged.plan_version,
            mode=changes["mode"] if "mode" in changes else merged.mode,
            goals=changes["goals"] if "goals" in changes else merged.goals,
            candidate_set_id=changes["candidate_set_id"]
            if "candidate_set_id" in changes
            else merged.candidate_set_id,
            requested_presentation=merged.requested_presentation,
            clarification_kind=merged.clarification_kind,
            search_action_requests=merged.search_action_requests,
            search_knowledge_requests=merged.search_knowledge_requests,
            context_references=merged.context_references,
        )

    @property
    def is_empty(self) -> bool:
        return not self.steps and not self.clarify

    @property
    def wants_search_round(self) -> bool:
        if self.mode in {"SEARCH_ACTIONS", "SEARCH_KNOWLEDGE", "SEARCH_MIXED"}:
            return True
        return bool(self.search_action_requests or self.search_knowledge_requests)
