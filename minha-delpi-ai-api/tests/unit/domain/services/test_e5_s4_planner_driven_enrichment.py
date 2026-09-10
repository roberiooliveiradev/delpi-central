"""E5.S4 — planner-driven enrichment via Goal Coverage retry (allowed-only)."""

from __future__ import annotations

from app.application.services.chat_goal_coverage_retry_service import (
    ChatGoalCoverageRetryService,
)


def _stock_action() -> dict:
    return {
        "actionId": "ext.products.stock",
        "whenToUse": "Use for «estoque», «saldo» or «disponível» of a product code.",
        "whenNotToUse": "Do not use for company-wide stock value.",
        "description": "Stock balance and warehouse positions.",
        "method": "GET",
        "path": "/products/{code}/stock",
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
        "method": "GET",
        "path": "/products/{code}/summary",
    }


def _sales_action() -> dict:
    return {
        "actionId": "ext.products.sales",
        "whenToUse": "Use for «vendas» of a product code.",
        "description": "Recent sales.",
        "method": "GET",
        "path": "/products/{code}/sales",
    }


def _stock_call(*, code: str = "10080011", data: dict | None = None) -> dict:
    payload = {
        "name": "execute_external_action",
        "arguments": {
            "actionId": "ext.products.stock",
            "parameters": {"code": code},
        },
        "ok": True,
        "metadata": {
            "ok": True,
            "actionId": "ext.products.stock",
            "path": f"/products/{code}/stock",
        },
    }
    if data is not None:
        payload["data"] = data
    return payload


def test_e5_s4_extra_action_necessary_for_mismatch():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[_stock_call()],
        remaining_slots=2,
        allowed_action_ids=[
            "ext.products.stock",
            "ext.products.summary",
            "ext.products.sales",
        ],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
            "ext.products.sales": _sales_action(),
        },
    )
    assert len(follow) == 1
    assert follow[0]["arguments"]["actionId"] == "ext.products.summary"
    meta = follow[0]["metadata"]
    assert meta["goalCoverageRetry"] is True
    assert meta["enrichmentReason"] == "goal_coverage_gap"
    assert meta["uncoveredGoalIds"] == ["g1"]
    assert meta["uncoveredStatuses"]["g1"] == "mismatch"


def test_e5_s4_extra_action_unnecessary_when_fulfilled():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="Consulte o estoque do produto 10080001",
        tool_calls=[
            _stock_call(
                code="10080001",
                data={"items": [{"wh": "01", "qty": 2}]},
            )
        ],
        remaining_slots=2,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert follow == []


def test_e5_s4_partial_pagination_does_not_auto_enrich():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="Consulte o estoque do produto 10080001",
        tool_calls=[
            _stock_call(
                code="10080001",
                data={
                    "items": [{"code": "A"}, {"code": "B"}],
                    "page": 1,
                    "page_size": 2,
                    "total": 40,
                    "total_pages": 20,
                },
            )
        ],
        remaining_slots=2,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert follow == []


def test_e5_s4_max_budget_caps_follow_ups():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[_stock_call()],
        remaining_slots=1,
        allowed_action_ids=[
            "ext.products.stock",
            "ext.products.summary",
            "ext.products.sales",
        ],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
            "ext.products.sales": _sales_action(),
        },
    )
    assert len(follow) == 1


def test_e5_s4_duplicate_action_suppressed():
    duplicate_stock = _stock_call()
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[duplicate_stock, dict(duplicate_stock)],
        remaining_slots=2,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert len(follow) == 1
    assert follow[0]["arguments"]["actionId"] == "ext.products.summary"
    assert follow[0]["arguments"]["actionId"] != "ext.products.stock"


def test_e5_s4_does_not_propose_outside_allowed():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[_stock_call()],
        remaining_slots=2,
        allowed_action_ids=["ext.products.stock"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert follow == []
