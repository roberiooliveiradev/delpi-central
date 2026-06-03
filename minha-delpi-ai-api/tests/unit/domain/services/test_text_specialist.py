"""Regressão especialista em textos / editor textual (T1–T28)."""

from __future__ import annotations

import pytest

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_text_task_service import ChatTextTaskService
from tests.fixtures.text_specialist_regression_cases import TEXT_SPECIALIST_REGRESSION_CASES


@pytest.mark.parametrize("case", TEXT_SPECIALIST_REGRESSION_CASES, ids=lambda c: c["id"])
def test_text_specialist_regression(case: dict):
    pure = ChatTextTaskIntentService.is_pure_text_task(case["message"])

    if case.get("mixed"):
        assert pure is False
        assert ChatTextTaskIntentService.is_mixed_text_and_operational(case["message"])
        return

    assert pure is case["pure"], f"{case['id']}: pure esperado {case['pure']}"

    category = ChatTextTaskIntentService.classify(case["message"])

    if case.get("category"):
        assert category == case["category"], f"{case['id']}: categoria {category}"

    route = ChatIntentRouterService.classify(
        case["message"],
        attachment_ids=case.get("attachment_ids"),
        text_task_pure=pure,
        text_task_category=category,
    )

    if pure:
        allowed = case.get("route_intents") or {"text_task", "email_task"}
        assert route.intent in allowed, case["id"]
        assert route.requires_tool is False or route.intent == "attachment_task"

    ctx = ChatTextTaskService.classify(case["message"])

    if case.get("final_only"):
        assert ctx.get("deliverFinalOnly") is True

    if case.get("preserved"):
        assert case["preserved"] in (ctx.get("preservedCodes") or [])

    if case.get("preference"):
        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        prefs = ChatTextTaskPreferenceService.detect_from_message(case["message"])
        assert prefs.get(case["preference"]) is True

    if case.get("subtype"):
        assert ctx.get("subtype") == case["subtype"], f"{case['id']}: subtype {ctx.get('subtype')}"

    if case.get("technical"):
        assert ctx.get("containsTechnicalTerms") is True, case["id"]

    if case.get("source"):
        assert ctx.get("source") == case["source"], f"{case['id']}: source {ctx.get('source')}"

    if case.get("intent"):
        assert ctx.get("intent") == case["intent"], f"{case['id']}: intent {ctx.get('intent')}"


def test_t1_router_blocks_operational():
    route = ChatIntentRouterService.classify("corrija: o produto esta bloqueado", text_task_pure=True)

    assert route.intent == "text_task"
    assert route.requires_tool is False


def test_text_quality_validator_preserves_code():
    from app.domain.services.chat_text_quality_validator import ChatTextQualityValidator

    quality = ChatTextQualityValidator.validate(
        "O produto 10080001 está bloqueado.",
        message="corrija: produto 10080001 esta bloqueado",
    )

    assert quality["passed"] is True
