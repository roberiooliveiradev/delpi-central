"""Evals F03 descrição vs estoque — R1/R2/R9/R11 determinísticos (sem LLM-judge)."""

from __future__ import annotations

import json
from pathlib import Path

from app.application.services.chat_goal_coverage_retry_service import (
    ChatGoalCoverageRetryService,
)
from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.chat_goal_coverage_service import ChatGoalCoverageService
from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "product_description_vs_stock_evals.json"
)


def _catalog() -> dict[str, dict]:
    return {
        "ext.products.stock": {
            "actionId": "ext.products.stock",
            "whenToUse": "Use for «estoque», «saldo» or «disponível» of a product code.",
            "whenNotToUse": "Do not use for company-wide stock value.",
            "description": "Stock balance and warehouse positions.",
            "path": "/items/{code}/balance",
        },
        "ext.products.summary": {
            "actionId": "ext.products.summary",
            "whenToUse": "Use for «descrição», «cadastro» or «ficha» of a product.",
            "whenNotToUse": (
                "Do not use when the user asked for «estoque», «saldo» or "
                "«disponível» — prefer the stock action."
            ),
            "description": "Light cadastro overview.",
            "path": "/items/{code}/overview",
        },
    }


def _load_cases() -> list[dict]:
    payload = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert payload["requiredDimensions"] == ["R1", "R2", "R9", "R11"]
    return list(payload["cases"])


def _stock_call(message_code: str = "10080011") -> dict:
    return {
        "name": "execute_external_action",
        "arguments": {
            "actionId": "ext.products.stock",
            "parameters": {"code": message_code},
        },
        "ok": True,
        "metadata": {"ok": True, "actionId": "ext.products.stock"},
    }


def test_family_corpus_declares_required_dimensions():
    cases = _load_cases()
    ids = {item["id"] for item in cases}
    assert "F03.descricao-code" in ids
    assert "F03.compound-estoque-descricao" in ids
    assert "F03.estoque-negative" in ids
    assert "F03.inspection-negative" in ids


def test_r1_r2_prefer_and_filter_match_expect():
    catalog = list(_catalog().values())
    for case in _load_cases():
        message = case["input"]
        expect = case["expect"]
        preferred = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
            message,
            catalog,
            raw_action_of=lambda item: item,
        )
        filtered = OpenApiWhenNotToUseGuidanceService.filter_candidates(
            message,
            catalog,
            raw_action_of=lambda item: item,
        )
        preferred_ids = [item["actionId"] for item in preferred]
        filtered_ids = {item["actionId"] for item in filtered}
        catalog_by_id = {item["actionId"]: item for item in catalog}
        for action_id in expect.get("preferActionIds") or []:
            assert action_id in preferred_ids
            assert action_id in filtered_ids
        for action_id in expect.get("forbidActionIds") or []:
            action = catalog_by_id[action_id]
            if expect.get("preferActionIds"):
                assert action_id not in preferred_ids
            else:
                assert not OpenApiWhenNotToUseGuidanceService.matches_positive(
                    message,
                    action,
                )
        if expect.get("minDistinctActions"):
            assert len(set(preferred_ids)) >= int(expect["minDistinctActions"])


def test_r9_http_ok_is_not_task_success_for_descricao():
    case = next(item for item in _load_cases() if item["id"] == "F03.descricao-code")
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent=case["input"]),),
        steps=(
            ActionPlanStep(
                action_id="ext.products.stock",
                goal_ids=("g1",),
                arguments={"parameters": {"code": "10080011"}},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[_stock_call()],
        message=case["input"],
        actions_by_id=_catalog(),
    )
    assert report.complete is False
    assert report.results[0].status == "mismatch"
    assert report.results[0].evidence_ok is False


def test_r11_correct_stock_does_not_retry():
    case = next(item for item in _load_cases() if item["id"] == "F03.estoque-negative")
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message=case["input"],
        tool_calls=[_stock_call("10080001")],
        remaining_slots=1,
        allowed_action_ids=list(_catalog().keys()),
        actions_by_id=_catalog(),
    )
    assert follow == []
