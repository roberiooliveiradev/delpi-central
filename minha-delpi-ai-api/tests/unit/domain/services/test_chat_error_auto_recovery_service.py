from app.domain.services.chat_error_auto_recovery_service import (
    ChatErrorAutoRecoveryService,
)


def test_build_plan_for_api_unavailable():
    plan = ChatErrorAutoRecoveryService.build_plan(
        error_type="api_unavailable",
        tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": "stock-action",
                    "parameters": {"productCode": "10080077"},
                },
                "metadata": {
                    "ok": False,
                    "statusCode": 503,
                    "actionId": "stock-action",
                    "path": "/products/10080077/stock",
                },
            }
        ],
    )

    assert plan is not None
    assert plan["strategy"] == "retry_last"
    assert plan["actionId"] == "stock-action"


def test_looks_like_recovery_request():
    assert ChatErrorAutoRecoveryService.looks_like_recovery_request(
        "tente novamente a consulta anterior",
    )


def test_apply_remove_filters_strategy():
    operation = {
        "actionId": "sales-action",
        "parameters": {"productCode": "10080001", "branch": "01", "period_start": "2026-01-01"},
    }

    parameters = ChatErrorAutoRecoveryService.apply_strategy(
        "remove_filters",
        operation,
        "repita a consulta sem filtros opcionais",
    )

    assert parameters.get("productCode") == "10080001"
    assert "branch" not in parameters
    assert "period_start" not in parameters
