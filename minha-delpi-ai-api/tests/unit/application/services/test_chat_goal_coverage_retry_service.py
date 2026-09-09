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


def _stock_call() -> dict:
    return {
        "name": "execute_external_action",
        "arguments": {
            "actionId": "ext.products.stock",
            "parameters": {"code": "10080011"},
        },
        "ok": True,
        "metadata": {"ok": True, "actionId": "ext.products.stock", "path": "/products/10080011/stock"},
    }


def test_retry_excludes_tried_stock_and_picks_summary_for_descricao():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[_stock_call()],
        remaining_slots=1,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert len(follow) == 1
    assert follow[0]["arguments"]["actionId"] == "ext.products.summary"
    assert follow[0]["arguments"]["parameters"]["code"] == "10080011"
    assert follow[0]["metadata"]["goalCoverageRetry"] is True


def test_correct_estoque_does_not_retry():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="Consulte o estoque do produto 10080001",
        tool_calls=[
            {
                **_stock_call(),
                "arguments": {
                    "actionId": "ext.products.stock",
                    "parameters": {"code": "10080001"},
                },
            }
        ],
        remaining_slots=1,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert follow == []


def test_no_retry_without_remaining_slots():
    follow = ChatGoalCoverageRetryService.plan_follow_ups(
        message="descrição 10080011",
        tool_calls=[_stock_call()],
        remaining_slots=0,
        allowed_action_ids=["ext.products.stock", "ext.products.summary"],
        actions_by_id={
            "ext.products.stock": _stock_action(),
            "ext.products.summary": _summary_action(),
        },
    )
    assert follow == []
