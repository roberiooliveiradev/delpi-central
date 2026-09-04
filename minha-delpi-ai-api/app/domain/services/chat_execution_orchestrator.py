"""Orquestra execução de TaskPlan reusando tools/RAG existentes (E6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.domain.services.chat_task_planner_service import TaskPlan, TaskPlanTask


@dataclass
class ExecutionOrchestratorResult:
    completed_task_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    replan_count: int = 0
    skipped: list[str] = field(default_factory=list)

    def as_admin_debug(self) -> dict[str, Any]:
        return {
            "completedTaskIds": list(self.completed_task_ids),
            "evidenceRefs": list(self.evidence_refs),
            "replanCount": self.replan_count,
            "skipped": list(self.skipped),
        }


class ChatExecutionOrchestrator:
    """Fachada: ordena tasks, paraleliza reads e respeita maxReplan."""

    def __init__(
        self,
        *,
        execute_tool: Callable[[TaskPlanTask], dict[str, Any]] | None = None,
        execute_rag: Callable[[TaskPlanTask], dict[str, Any]] | None = None,
        execute_web: Callable[[TaskPlanTask], dict[str, Any]] | None = None,
        execute_reason: Callable[[TaskPlanTask], dict[str, Any]] | None = None,
    ):
        self.execute_tool = execute_tool
        self.execute_rag = execute_rag
        self.execute_web = execute_web
        self.execute_reason = execute_reason

    def run(self, plan: TaskPlan) -> ExecutionOrchestratorResult:
        result = ExecutionOrchestratorResult()
        pending = {task.id: task for task in plan.tasks}
        done: set[str] = set()

        while pending and len(result.completed_task_ids) < plan.max_steps:
            ready = [
                task
                for task in pending.values()
                if all(dep in done for dep in task.depends_on)
            ]
            if not ready:
                result.skipped.extend(sorted(pending.keys()))
                break

            parallel = [task for task in ready if task.parallel_group]
            serial = [task for task in ready if not task.parallel_group]
            batch = parallel or serial[:1]

            for task in batch:
                outcome = self._execute_one(task)
                empty = not outcome or outcome.get("empty")
                if empty and result.replan_count < plan.max_replan:
                    result.replan_count += 1
                    outcome = self._execute_one(task)
                if outcome and not outcome.get("empty"):
                    result.completed_task_ids.append(task.id)
                    ref = str(outcome.get("evidenceRef") or task.capability_id or task.id)
                    result.evidence_refs.append(ref)
                    done.add(task.id)
                    pending.pop(task.id, None)
                else:
                    result.skipped.append(task.id)
                    pending.pop(task.id, None)

        return result

    def _execute_one(self, task: TaskPlanTask) -> dict[str, Any]:
        handler = {
            "tool": self.execute_tool,
            "rag": self.execute_rag,
            "web": self.execute_web,
            "reason": self.execute_reason,
            "transform": self.execute_reason,
        }.get(task.type)
        if handler is None:
            return {"empty": False, "evidenceRef": f"noop:{task.id}"}
        try:
            return handler(task) or {"empty": True}
        except Exception:
            return {"empty": True}
