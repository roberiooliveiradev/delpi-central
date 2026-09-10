"""E5.S3 — contrato canônico de Goal Coverage (facts/metadata, sem path authority)."""

from __future__ import annotations

from app.domain.models.action_plan import ActionPlan, ActionPlanGoal, ActionPlanStep
from app.domain.services.chat_goal_coverage_service import ChatGoalCoverageService


def _stock_action() -> dict:
    return {
        "actionId": "ext.products.stock",
        "whenToUse": "Use for «estoque», «saldo» or «disponível» of a product code.",
        "whenNotToUse": "Do not use for company-wide stock value.",
        "description": "Stock balance and warehouse positions.",
    }


def _summary_action() -> dict:
    return {
        "actionId": "ext.acme.unknown_summary",
        "whenToUse": "Use for «descrição», «cadastro» or «ficha» of a product.",
        "whenNotToUse": (
            "Do not use when the user asked for «estoque», «saldo» or "
            "«disponível» — prefer the stock action."
        ),
        "description": "Unknown external API cadastro overview.",
        "delpi_metadata": {
            "uxCapability": {"category": "Product profile", "examples": []},
        },
    }


def test_e5_s3_empty_payload_is_needs_more_data():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque"),),
        steps=(
            ActionPlanStep(action_id="ext.products.stock", goal_ids=("g1",), arguments={}),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": True,
                "metadata": {"ok": True},
                "data": {"items": []},
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={"ext.products.stock": _stock_action()},
    )
    assert report.complete is False
    assert report.results[0].status == "needs_more_data"
    assert report.needs_more_data_goal_ids == ("g1",)
    assert report.failed_goal_ids == ()


def test_e5_s3_partial_pagination_from_result_facts():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque"),),
        steps=(
            ActionPlanStep(action_id="ext.products.stock", goal_ids=("g1",), arguments={}),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": True,
                "metadata": {"ok": True},
                "data": {
                    "items": [{"code": "A"}, {"code": "B"}],
                    "page": 1,
                    "page_size": 2,
                    "total": 40,
                    "total_pages": 20,
                },
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={"ext.products.stock": _stock_action()},
    )
    assert report.complete is False
    assert report.results[0].status == "partial"
    assert report.partial_goal_ids == ("g1",)
    assert report.results[0].evidence_ok is True


def test_e5_s3_sibling_schema_fulfills_without_path_authority():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="cadastro do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.acme.unknown_summary",
                goal_ids=("g1",),
                arguments={"code": "10080011"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.acme.unknown_summary",
                "ok": True,
                "metadata": {"ok": True},
                "data": {"code": "10080011", "description": "Terminal"},
            }
        ],
        message="cadastro do produto 10080011",
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.acme.unknown_summary": _summary_action(),
        },
    )
    assert report.complete is True
    assert report.results[0].status == "fulfilled"


def test_e5_s3_unknown_api_mismatch_still_uses_when_not_to_use():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.acme.unknown_summary",
                goal_ids=("g1",),
                arguments={"code": "10080001"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.acme.unknown_summary",
                "ok": True,
                "metadata": {"ok": True},
                "data": {"code": "10080001"},
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.acme.unknown_summary": _summary_action(),
        },
    )
    assert report.complete is False
    assert report.results[0].status == "mismatch"


def test_e5_s3_blocked_goal_and_forbidden_execution():
    blocked_plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque", status="blocked"),),
        steps=(),
    )
    blocked = ChatGoalCoverageService.evaluate(
        blocked_plan,
        execution_results=[],
        message="estoque 10080001",
    )
    assert blocked.results[0].status == "blocked"
    assert blocked.blocked_goal_ids == ("g1",)

    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque"),),
        steps=(
            ActionPlanStep(action_id="ext.products.stock", goal_ids=("g1",), arguments={}),
        ),
    )
    forbidden = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": False,
                "metadata": {"ok": False, "statusCode": 403},
            }
        ],
        message="estoque 10080001",
        actions_by_id={"ext.products.stock": _stock_action()},
    )
    assert forbidden.results[0].status == "blocked"
    assert forbidden.blocked_goal_ids == ("g1",)


def test_e5_s3_fulfilled_non_empty_is_complete():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque"),),
        steps=(
            ActionPlanStep(action_id="ext.products.stock", goal_ids=("g1",), arguments={}),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": True,
                "metadata": {"ok": True},
                "data": {"items": [{"wh": "01", "qty": 3}]},
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={"ext.products.stock": _stock_action()},
    )
    assert report.complete is True
    assert report.results[0].status == "fulfilled"
