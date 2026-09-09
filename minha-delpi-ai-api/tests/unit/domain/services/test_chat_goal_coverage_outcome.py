"""Goal coverage after execute — HTTP ok is not task success (R9)."""

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
        "actionId": "ext.products.summary",
        "whenToUse": "Use for «descrição», «cadastro» or «ficha» of a product.",
        "whenNotToUse": (
            "Do not use when the user asked for «estoque», «saldo» or "
            "«disponível» — prefer the stock action."
        ),
        "description": "Light cadastro overview.",
    }


def test_http_ok_stock_does_not_fulfill_descricao_request():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="descrição do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.products.stock",
                goal_ids=("g1",),
                arguments={"path": "/products/10080011/stock"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": True,
                "metadata": {"ok": True, "path": "/products/10080011/stock"},
            }
        ],
        message="descrição 10080011",
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert report.complete is False
    assert report.results[0].status == "mismatch"


def test_http_ok_stock_fulfills_estoque_request():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.products.stock",
                goal_ids=("g1",),
                arguments={"path": "/products/10080001/stock"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.stock",
                "ok": True,
                "metadata": {"ok": True},
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={"ext.products.stock": _stock_action()},
    )
    assert report.complete is True
    assert report.results[0].status == "fulfilled"


def test_http_ok_summary_does_not_fulfill_estoque_via_when_not_to_use():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="estoque do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.products.summary",
                goal_ids=("g1",),
                arguments={"path": "/products/10080001/summary"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.summary",
                "ok": True,
                "metadata": {"ok": True},
            }
        ],
        message="Consulte o estoque do produto 10080001",
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert report.complete is False
    assert report.results[0].status == "mismatch"


def test_http_ok_summary_fulfills_cadastro_sibling():
    plan = ActionPlan(
        goals=(ActionPlanGoal(goal_id="g1", intent="cadastro do produto"),),
        steps=(
            ActionPlanStep(
                action_id="ext.products.summary",
                goal_ids=("g1",),
                arguments={"path": "/products/10080011/summary"},
            ),
        ),
    )
    report = ChatGoalCoverageService.evaluate(
        plan,
        execution_results=[
            {
                "actionId": "ext.products.summary",
                "ok": True,
                "metadata": {"ok": True},
            }
        ],
        message="cadastro do produto 10080011",
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert report.complete is True
    assert report.results[0].status == "fulfilled"


def test_empty_payload_is_not_fulfilled():
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
