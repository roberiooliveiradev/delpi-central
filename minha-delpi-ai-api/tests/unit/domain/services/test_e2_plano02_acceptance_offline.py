"""E2 aceite plano-02 — critérios offline do plano (positive/sibling/negative)."""

from __future__ import annotations

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_task_planner_service import ChatTaskPlannerService
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService
from app.domain.services.turn_understanding_product_intent_mapper_service import (
    TurnUnderstandingProductIntentMapperService,
)


def test_long_compound_request_splits_and_plans() -> None:
    message = (
        "1. estoque do produto 10080001\n"
        "2. fornecedores desse produto\n"
        "3. resume os achados"
    )
    understanding = ChatTurnUnderstandingService.analyze(message)
    assert understanding.subtask_count >= 2
    plan = ChatTaskPlannerService.plan_for_execution(message, response_mode="normal")
    assert plan is not None
    assert plan.task_count >= 2


def test_typo_synonym_generalization_stock() -> None:
    typo = "estoque do prodtuo 10080001"
    synonym = "saldo disponível do 10080001"
    assert ChatProductQueryIntentService.detect(synonym) == "stock"
    # typo still resolves via mapper or legacy stock/full without path enum
    assert ChatProductQueryIntentService.detect(typo) in {"stock", "full"}
    assert TurnUnderstandingProductIntentMapperService.from_message(synonym) == "stock"


def test_no_tool_smalltalk() -> None:
    route = ChatIntentRouterService.classify("oi, tudo bem?")
    assert route.intent == "small_talk"
    assert route.requires_tool is False


def test_semantic_siblings_presentation_and_compare() -> None:
    table = ChatIntentRouterService.classify("quero ver em tabela")
    assert table.intent == "text_task"
    assert table.sub_intent == "table"
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "compara o estoque deste mês com o mês passado"
    )


def test_no_endpoint_intent_enum_in_tu_contract() -> None:
    contract = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    payload = contract.as_dict()
    blob = str(payload).lower()
    assert "pathtoken" not in blob
    assert "operationid" not in blob
    assert all(goal.kind in {"lookup", "action", "reasoning", "unknown"} for goal in contract.goals)
