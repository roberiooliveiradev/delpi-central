"""TaskPlan a partir de TurnUnderstanding + discovery (E5) — shadow/cutover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)
from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
    TurnUnderstanding,
)


@dataclass(frozen=True)
class TaskPlanTask:
    id: str
    goal: str
    type: str
    capability_id: str | None = None
    depends_on: tuple[str, ...] = ()
    parallel_group: str | None = None
    status: str = "pending"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "type": self.type,
            "capabilityId": self.capability_id,
            "dependsOn": list(self.depends_on),
            "parallelGroup": self.parallel_group,
            "status": self.status,
        }


@dataclass(frozen=True)
class TaskPlan:
    tasks: tuple[TaskPlanTask, ...]
    max_steps: int
    max_replan: int
    source: str = "heuristic"

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tasks": [task.as_dict() for task in self.tasks],
            "maxSteps": self.max_steps,
            "maxReplan": self.max_replan,
            "source": self.source,
            "taskCount": self.task_count,
        }

    def as_admin_debug(self) -> dict[str, Any]:
        return self.as_dict()


class ChatTaskPlannerService:
    _REPLAN_BY_MODE = {"fast": 0, "normal": 1, "thinker": 2}
    _STEPS_BY_MODE = {"fast": 1, "normal": 4, "thinker": 8}

    @classmethod
    def build_from_understanding(
        cls,
        understanding: TurnUnderstanding,
        *,
        message: str,
        response_mode: str | None = None,
    ) -> TaskPlan:
        mode = str(response_mode or "normal").strip().lower() or "normal"
        max_steps = cls._STEPS_BY_MODE.get(mode, 4)
        max_replan = cls._REPLAN_BY_MODE.get(mode, 1)
        discovery = ChatCapabilityDiscoveryService.discover(message)
        candidates = list(discovery.candidates)
        tasks: list[TaskPlanTask] = []

        for index, subtask in enumerate(understanding.subtasks[:max_steps], start=1):
            capability_id = cls._match_capability(subtask.goal, candidates)
            task_type = cls._map_type(subtask.type, capability_id)
            depends = tuple(subtask.depends_on)
            if index > 1 and not depends and cls._needs_prior_code(subtask.goal):
                depends = (f"t-{index - 1}",)
            tasks.append(
                TaskPlanTask(
                    id=f"t-{index}",
                    goal=subtask.goal,
                    type=task_type,
                    capability_id=capability_id,
                    depends_on=depends,
                    parallel_group="reads" if task_type == "tool" and not depends else None,
                )
            )

        if not tasks:
            tasks = [
                TaskPlanTask(
                    id="t-1",
                    goal=understanding.user_goal,
                    type="reason",
                    capability_id="transform.reason",
                )
            ]

        return TaskPlan(
            tasks=tuple(tasks),
            max_steps=max_steps,
            max_replan=max_replan,
            source="heuristic",
        )

    @classmethod
    def plan_shadow(
        cls,
        message: str,
        *,
        response_mode: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> TaskPlan | None:
        understanding = ChatTurnUnderstandingService.analyze(
            message,
            response_mode=response_mode,
            previous_messages=previous_messages,
        )
        return cls.build_from_understanding(
            understanding,
            message=message,
            response_mode=response_mode,
        )

    @classmethod
    def plan_for_execution(
        cls,
        message: str,
        *,
        response_mode: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> TaskPlan | None:
        if not ChatConversationalIntelligenceFlagService.task_planner_enabled():
            return None
        if str(response_mode or "").strip().lower() == "fast":
            return None
        return cls.plan_shadow(
            message,
            response_mode=response_mode,
            previous_messages=previous_messages,
        )

    @classmethod
    def _match_capability(
        cls,
        goal: str,
        candidates: list[dict[str, Any]],
    ) -> str | None:
        discovery = ChatCapabilityDiscoveryService.discover(goal, top_k=3)
        if discovery.candidates:
            return str(discovery.candidates[0].get("capabilityId") or "") or None
        if candidates:
            return str(candidates[0].get("capabilityId") or "") or None
        return None

    @classmethod
    def _map_type(cls, subtask_type: str, capability_id: str | None) -> str:
        if capability_id and capability_id.startswith("rag."):
            return "rag"
        if capability_id and capability_id.startswith("web."):
            return "web"
        if capability_id and capability_id.startswith("action."):
            return "tool"
        if subtask_type == "reasoning":
            return "reason"
        if subtask_type == "action":
            return "tool"
        return "reason"

    @classmethod
    def _needs_prior_code(cls, goal: str) -> bool:
        lowered = goal.lower()
        return any(
            token in lowered
            for token in ("estoque", "segundo", "primeiro", "desse", "dele", "normas")
        )
