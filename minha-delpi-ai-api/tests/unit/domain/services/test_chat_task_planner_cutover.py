"""E4.S1/E4.S2/E5.S2/E6 — registry, discovery, cutover por flag e orquestração."""

from __future__ import annotations

from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)
from app.domain.services.chat_capability_registry_service import (
    ChatCapabilityRegistryService,
)
from app.domain.services.chat_execution_orchestrator import ChatExecutionOrchestrator
from app.domain.services.chat_task_planner_content_service import (
    ChatTaskPlannerContentService,
)
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService


# ---------------------------------------------------------------- E4.S1 registry


def test_registry_loader_counts_by_type():
    assert ChatCapabilityRegistryService.count() >= 5
    assert len(ChatCapabilityRegistryService.by_type("action")) >= 3
    assert len(ChatCapabilityRegistryService.by_type("rag")) >= 1
    assert len(ChatCapabilityRegistryService.by_type("web")) >= 1
    assert ChatCapabilityRegistryService.by_type("nonexistent") == []


def test_registry_capabilities_expose_thin_route_hints_not_full_registry():
    for capability in ChatCapabilityRegistryService.all_capabilities():
        assert capability.get("descriptionForModel")
        assert "operationId" not in capability


# -------------------------------------------------------------- E4.S2 discovery


def test_discovery_ranks_product_search_for_terminais_pino():
    result = ChatCapabilityDiscoveryService.discover("liste terminais pino")
    ids = [str(item.get("capabilityId") or "") for item in result.candidates]

    assert "action.product_search" in ids


def test_discovery_type_filter_records_discard_reason():
    result = ChatCapabilityDiscoveryService.discover(
        "liste terminais pino",
        allowed_types={"rag"},
    )
    reasons = {item["capabilityId"]: item["reason"] for item in result.discard_reasons}

    assert reasons.get("action.product_search") == "type_filtered"


def test_discovery_discards_irrelevant_capabilities_with_reason():
    result = ChatCapabilityDiscoveryService.discover("estoque do produto 10080001")
    reasons = {item["reason"] for item in result.discard_reasons}

    assert reasons
    assert reasons <= {"low_relevance", "type_filtered"}


def test_discovery_respects_top_k():
    result = ChatCapabilityDiscoveryService.discover("liste terminais pino", top_k=1)

    assert len(result.candidates) <= 1


# ------------------------------------------------------- E5.S2 cutover por flag


def test_planner_execution_disabled_by_default_flag(monkeypatch):
    monkeypatch.delenv("CHAT_TASK_PLANNER_ENABLED", raising=False)

    assert ChatTaskPlannerService.plan_for_execution("liste terminais pino") is None


def test_planner_execution_enabled_by_env_override(monkeypatch):
    monkeypatch.setenv("CHAT_TASK_PLANNER_ENABLED", "true")

    plan = ChatTaskPlannerService.plan_for_execution(
        "liste terminais pino; mostre o estoque do segundo",
        response_mode="normal",
    )

    assert plan is not None
    assert plan.task_count >= 2


def test_fast_mode_never_enters_planner_execution(monkeypatch):
    monkeypatch.setenv("CHAT_TASK_PLANNER_ENABLED", "true")

    assert (
        ChatTaskPlannerService.plan_for_execution(
            "liste terminais pino; estoque do segundo",
            response_mode="fast",
        )
        is None
    )


def test_fast_mode_shadow_plan_stays_single_step():
    plan = ChatTaskPlannerService.plan_shadow(
        "liste terminais pino; estoque do segundo; compare os dois",
        response_mode="fast",
    )

    assert plan is not None
    assert plan.max_steps == 1
    assert plan.task_count == 1
    assert plan.max_replan == 0


def test_single_intent_message_keeps_one_task():
    plan = ChatTaskPlannerService.plan_shadow(
        "qual o estoque do produto 10080001?",
        response_mode="normal",
    )

    assert plan is not None
    assert plan.task_count == 1
    assert plan.tasks[0].depends_on == ()


def test_planner_limits_come_from_content_bundle():
    assert ChatTaskPlannerContentService.mode_limit_int("maxStepsByMode", "thinker", 0) >= 4
    assert ChatTaskPlannerContentService.string_list("priorCodeMarkers")
    assert "fast" in ChatTaskPlannerContentService.string_list("executionDisabledModes")


# ------------------------------------------------------ E6 execução orquestrada


def test_orchestrator_respects_dependency_order():
    plan = ChatTaskPlannerService.plan_shadow(
        "1) liste terminais pino\n2) mostre o estoque do segundo",
        response_mode="normal",
    )
    executed: list[str] = []

    def handler(task):
        executed.append(task.id)
        return {"empty": False, "evidenceRef": f"tool:{task.id}"}

    result = ChatExecutionOrchestrator(
        execute_tool=handler,
        execute_rag=handler,
        execute_web=handler,
        execute_reason=handler,
    ).run(plan)

    dependent = [task for task in plan.tasks if task.depends_on]

    assert result.completed_task_ids
    for task in dependent:
        for dependency in task.depends_on:
            if dependency in executed and task.id in executed:
                assert executed.index(dependency) < executed.index(task.id)


def test_orchestrator_caps_replan_attempts():
    plan = ChatTaskPlannerService.plan_shadow(
        "liste terminais pino; estoque do segundo",
        response_mode="normal",
    )
    calls = {"count": 0}

    def always_empty(task):
        calls["count"] += 1
        return {"empty": True}

    result = ChatExecutionOrchestrator(
        execute_tool=always_empty,
        execute_rag=always_empty,
        execute_web=always_empty,
        execute_reason=always_empty,
    ).run(plan)

    assert result.replan_count <= plan.max_replan
    assert result.skipped


def test_orchestrator_survives_handler_exception():
    plan = ChatTaskPlannerService.plan_shadow("liste terminais pino", response_mode="normal")

    def broken(task):
        raise RuntimeError("falha simulada de tool")

    result = ChatExecutionOrchestrator(
        execute_tool=broken,
        execute_rag=broken,
        execute_web=broken,
        execute_reason=broken,
    ).run(plan)

    assert result.completed_task_ids == []
    assert "replanCount" in result.as_admin_debug()
