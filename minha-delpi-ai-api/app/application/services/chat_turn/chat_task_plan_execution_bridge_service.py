"""Ponte cutover: TaskPlan → ExecutionOrchestrator (sem HTTP direto).

Quando ``CHAT_TASK_PLANNER_ENABLED`` produz um plano ativo, este serviço
executa o orquestrador com handlers de *schedule* (não bypassam RBAC nem
``ExecuteExternalActionUseCase``). O resultado alimenta adminDebug e a ordem
de capabilities para o loop de tools já existente.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_execution_orchestrator import (
    ChatExecutionOrchestrator,
    ExecutionOrchestratorResult,
)
from app.domain.services.chat_task_planner_service import TaskPlan, TaskPlanTask


class ChatTaskPlanExecutionBridgeService:
    @classmethod
    def run_scheduled(cls, plan: TaskPlan) -> dict[str, Any]:
        """Roda o orquestrador e devolve payload para ``workspace_context``."""
        orchestrator = ChatExecutionOrchestrator(
            execute_tool=cls._schedule,
            execute_rag=cls._schedule,
            execute_web=cls._schedule,
            execute_reason=cls._schedule,
        )
        result = orchestrator.run(plan)
        return cls._payload(plan, result)

    @classmethod
    def _schedule(cls, task: TaskPlanTask) -> dict[str, Any]:
        capability = str(task.capability_id or "").strip() or f"task:{task.id}"
        return {
            "empty": False,
            "evidenceRef": f"scheduled:{capability}",
            "capabilityId": capability,
            "taskId": task.id,
            "goal": task.goal,
            "type": task.type,
        }

    @classmethod
    def _payload(
        cls,
        plan: TaskPlan,
        result: ExecutionOrchestratorResult,
    ) -> dict[str, Any]:
        ordered = [
            str(task.capability_id or task.id)
            for task in plan.tasks
            if task.id in set(result.completed_task_ids)
        ]
        return {
            "executionOrchestrator": result.as_admin_debug(),
            "replanCount": result.replan_count,
            "taskPlanCapabilityOrder": ordered,
        }
