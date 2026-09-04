from app.application.services.chat_turn.chat_task_plan_execution_bridge_service import (
    ChatTaskPlanExecutionBridgeService,
)
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import (
    ChatTurnUnderstandingService,
)


def test_bridge_runs_orchestrator_and_exposes_order():
    understanding = ChatTurnUnderstandingService.analyze(
        "1) liste terminais pino\n2) estoque do segundo"
    )
    plan = ChatTaskPlannerService.build_from_understanding(
        understanding,
        message="1) liste terminais pino\n2) estoque do segundo",
        response_mode="normal",
    )

    payload = ChatTaskPlanExecutionBridgeService.run_scheduled(plan)

    assert "executionOrchestrator" in payload
    assert isinstance(payload["replanCount"], int)
    assert isinstance(payload["taskPlanCapabilityOrder"], list)
    assert payload["executionOrchestrator"]["completedTaskIds"]
