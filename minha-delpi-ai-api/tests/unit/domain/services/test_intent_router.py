"""Regressão Playbook 02 — roteamento inteligente de intenção (R1–R15)."""

from __future__ import annotations

import pytest

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from tests.fixtures.intent_router_regression_cases import INTENT_ROUTER_REGRESSION_CASES


@pytest.mark.parametrize("case", INTENT_ROUTER_REGRESSION_CASES, ids=lambda c: c["id"])
def test_intent_router_regression(case: dict):
    route = ChatIntentRouterService.classify(
        case["message"],
        previous_messages=case.get("history"),
        attachment_ids=case.get("attachment_ids"),
        workspace_context=case.get("workspace_context"),
        allowed_action_ids=case.get("allowed_action_ids") or ["action-1"],
        text_task_pure=case.get("text_task_pure", False),
        text_task_category=case.get("text_task_category"),
    )

    assert route.intent == case["expected_intent"], (
        f"{case['id']}: esperado {case['expected_intent']}, obteve {route.intent}"
    )

    if case.get("expected_sub_intent"):
        assert route.sub_intent == case["expected_sub_intent"]

    if case.get("is_follow_up"):
        assert route.is_follow_up is True

    if case.get("requires_tool") is False:
        assert route.requires_tool is False

    if case.get("requires_web"):
        assert route.requires_web is True

    if case.get("requires_canvas"):
        assert route.requires_canvas is True

    if case.get("expected_product_code"):
        assert (route.resolved_params or {}).get("productCode") == case["expected_product_code"]

    if case.get("expected_ambiguous") is False:
        assert route.ambiguous is False

    payload = route.to_dict()
    assert "intentRouting" in payload
    assert payload["intentRouting"]["intent"] == case["expected_intent"]


def test_text_correction_beats_operational_stock_phrase():
    route = ChatIntentRouterService.classify("Corrija: o estoque esta baixo")

    assert route.intent == "text_task"
    assert route.requires_tool is False
    assert route.to_dict()["router"]["reason"] == "explicit_text_task"


def test_mixed_task_has_steps():
    route = ChatIntentRouterService.classify(
        "Consulte o estoque do produto 10080001 e escreva um e-mail para compras"
    )

    assert route.intent == "mixed_task"
    assert route.mixed_steps
    assert "stock_lookup" in route.mixed_steps
    assert "email_create" in route.mixed_steps


def test_web_blocked_when_user_requests_no_search():
    route = ChatIntentRouterService.classify(
        "Não pesquise na web — só me diga o que sabe sobre WEG"
    )

    assert route.intent != "web_search"


def test_resolve_executed_maps_capabilities_stage_to_self_help():
    route = ChatIntentRouterService.resolve_executed(
        message="o que você pode fazer?",
        pipeline_stages=["ingress", "capabilities", "direct_answer"],
        direct_answer="Catálogo",
        skip_rag=True,
    )

    assert route.intent == "self_help"
