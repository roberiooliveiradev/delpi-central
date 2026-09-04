from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)
from app.domain.services.chat_capability_registry_service import (
    ChatCapabilityRegistryService,
)
from app.domain.services.chat_execution_orchestrator import ChatExecutionOrchestrator
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
)


def test_capability_registry_has_core_entries():
    assert ChatCapabilityRegistryService.count() >= 5
    assert ChatCapabilityRegistryService.by_id("action.product_search")


def test_discovery_terminais_pino_includes_product_search():
    result = ChatCapabilityDiscoveryService.discover("liste terminais pino")
    ids = {str(item.get("capabilityId") or "") for item in result.candidates}
    assert "action.product_search" in ids


def test_task_plan_search_to_stock_dependency():
    message = (
        "1) liste terminais pino\n"
        "2) mostre o estoque do segundo"
    )
    understanding = ChatTurnUnderstandingService.analyze(message)
    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message=message,
        response_mode="normal",
    )
    assert plan.task_count >= 2
    assert any(task.depends_on for task in plan.tasks[1:])


def test_execution_orchestrator_orders_and_replans():
    attempts = {"tool": 0}

    def tool_handler(task):
        attempts["tool"] += 1
        if attempts["tool"] == 1:
            return {"empty": True}
        return {"empty": False, "evidenceRef": f"tool:{task.id}"}

    understanding = ChatTurnUnderstandingService.analyze("liste terminais; estoque do segundo")
    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message="liste terminais; estoque do segundo",
        response_mode="normal",
    )
    orchestrator = ChatExecutionOrchestrator(execute_tool=tool_handler)
    result = orchestrator.run(plan)
    assert result.replan_count >= 1 or result.completed_task_ids
    assert result.as_admin_debug()["replanCount"] >= 0
