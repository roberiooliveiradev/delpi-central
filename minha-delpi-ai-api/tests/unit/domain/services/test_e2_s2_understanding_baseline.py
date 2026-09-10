"""E2.S2 — baseline freeze: authority intents vs Turn Understanding shadow.

Does not promote TU to authority. Freezes observable pairs for families required
by plano 02 (short/long, compound, typo, synonym, no-tool, RAG, presentation,
production, compare).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
)
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService


@dataclass(frozen=True)
class BaselineCase:
    family: str
    message: str
    intent: str
    sub_intent: str | None
    requires_tool: bool
    product_intent: str
    production_kind: str | None
    tu_subtask_count: int
    tu_types: tuple[str, ...]
    is_compare: bool


# Frozen 2026-09-10 against HEAD intent routers + heuristic TU.
_CORPUS: tuple[BaselineCase, ...] = (
    BaselineCase(
        family="stock_short",
        message="qual o estoque do produto 10080001?",
        intent="operational_query",
        sub_intent="stock_lookup",
        requires_tool=True,
        product_intent="stock",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("lookup",),
        is_compare=False,
    ),
    BaselineCase(
        family="stock_typo",
        message="qual o estoqe do produto 10080001?",
        intent="operational_query",
        sub_intent="stock_lookup",
        requires_tool=True,
        product_intent="stock",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("lookup",),
        is_compare=False,
    ),
    BaselineCase(
        family="synonym_balance",
        message="saldo disponível do 10080001",
        intent="operational_query",
        sub_intent="stock_lookup",
        requires_tool=True,
        product_intent="stock",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("unknown",),
        is_compare=False,
    ),
    BaselineCase(
        family="compound_enum",
        message=(
            "1. estoque do 10080001\n"
            "2. fornecedores desse produto\n"
            "3. envia resumo por e-mail"
        ),
        intent="mixed_task",
        sub_intent="operational_then_text",
        requires_tool=True,
        product_intent="multi_scope",
        production_kind=None,
        tu_subtask_count=3,
        tu_types=("unknown", "unknown", "action"),
        is_compare=False,
    ),
    BaselineCase(
        family="compound_semi",
        message="estoque do 10080001; fornecedores do 10080001",
        intent="operational_query",
        sub_intent="supplier_lookup",
        requires_tool=True,
        product_intent="multi_scope",
        production_kind=None,
        tu_subtask_count=2,
        tu_types=("unknown", "unknown"),
        is_compare=False,
    ),
    BaselineCase(
        family="no_tool_smalltalk",
        message="oi, tudo bem?",
        intent="small_talk",
        sub_intent=None,
        requires_tool=False,
        product_intent="full",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("unknown",),
        is_compare=False,
    ),
    BaselineCase(
        family="presentation_table",
        message="mostra isso em tabela",
        intent="follow_up",
        sub_intent="format_refinement",
        requires_tool=False,
        product_intent="full",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("lookup",),
        is_compare=False,
    ),
    BaselineCase(
        family="rag_policy",
        message="o que diz a política de compras?",
        intent="rag_question",
        sub_intent=None,
        requires_tool=False,
        product_intent="full",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("unknown",),
        is_compare=False,
    ),
    BaselineCase(
        family="production_schedule",
        message="programação de produção hoje",
        intent="operational_query",
        sub_intent="schedule_today_lookup",
        requires_tool=True,
        product_intent="full",
        production_kind="SCHEDULE_TODAY",
        tu_subtask_count=1,
        tu_types=("unknown",),
        is_compare=False,
    ),
    BaselineCase(
        family="compare_insight",
        message="compara o estoque deste mês com o mês passado",
        intent="operational_query",
        sub_intent="analysis",
        requires_tool=True,
        product_intent="stock",
        production_kind=None,
        tu_subtask_count=1,
        tu_types=("reasoning",),
        is_compare=True,
    ),
)


def _observe(message: str) -> dict:
    route = ChatIntentRouterService.classify(message)
    production = ChatProductionOperationalIntentService.resolve(message)
    understanding = ChatTurnUnderstandingService.analyze(message)
    return {
        "intent": route.intent,
        "sub_intent": route.sub_intent,
        "requires_tool": bool(route.requires_tool),
        "product_intent": ChatProductQueryIntentService.detect(message),
        "production_kind": None if production is None else production.name,
        "tu_subtask_count": understanding.subtask_count,
        "tu_types": tuple(item.type for item in understanding.subtasks),
        "is_compare": ChatAnalysisIntentService.is_comparison_or_insight_request(message),
    }


def test_e2_s2_baseline_corpus_covers_required_families():
    families = {case.family for case in _CORPUS}
    required = {
        "stock_short",
        "stock_typo",
        "synonym_balance",
        "compound_enum",
        "compound_semi",
        "no_tool_smalltalk",
        "presentation_table",
        "rag_policy",
        "production_schedule",
        "compare_insight",
    }
    assert required <= families
    assert len(_CORPUS) >= 10


def test_e2_s2_authority_and_shadow_tu_match_frozen_baseline():
    mismatches: list[tuple[str, dict, dict]] = []
    for case in _CORPUS:
        observed = _observe(case.message)
        expected = {
            "intent": case.intent,
            "sub_intent": case.sub_intent,
            "requires_tool": case.requires_tool,
            "product_intent": case.product_intent,
            "production_kind": case.production_kind,
            "tu_subtask_count": case.tu_subtask_count,
            "tu_types": case.tu_types,
            "is_compare": case.is_compare,
        }
        if observed != expected:
            mismatches.append((case.family, expected, observed))
    assert not mismatches, mismatches


def test_e2_s2_compound_recall_shadow_splits_enumerated_goals():
    case = next(item for item in _CORPUS if item.family == "compound_enum")
    understanding = ChatTurnUnderstandingService.analyze(case.message)
    assert understanding.subtask_count >= 3
    goals = " ".join(item.goal for item in understanding.subtasks)
    assert "10080001" in goals
    assert "fornecedores" in goals.lower()
    assert "e-mail" in goals.lower() or "email" in goals.lower()


def test_e2_s2_no_tool_negative_does_not_require_tool():
    case = next(item for item in _CORPUS if item.family == "no_tool_smalltalk")
    route = ChatIntentRouterService.classify(case.message)
    assert route.requires_tool is False
    assert route.intent == "small_talk"


def test_e2_s2_typo_sibling_keeps_stock_authority():
    short = next(item for item in _CORPUS if item.family == "stock_short")
    typo = next(item for item in _CORPUS if item.family == "stock_typo")
    assert _observe(short.message)["product_intent"] == "stock"
    assert _observe(typo.message)["product_intent"] == "stock"
