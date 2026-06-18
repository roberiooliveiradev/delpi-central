from unittest.mock import MagicMock

from app.application.services.chat_playbook_product_action_readiness_service import (
    ChatPlaybookProductActionReadinessService,
)


def test_matches_factory_status_playbook_intent():
    assert ChatPlaybookProductActionReadinessService.matches_playbook_product_intent(
        "status fabril do produto 90269002 hoje"
    )


def test_gap_answer_when_factory_status_missing_from_catalog():
    repository = MagicMock()
    repository.list_actions.return_value = []

    answer = ChatPlaybookProductActionReadinessService.resolve_gap_direct_answer(
        "status fabril do produto 90269002 hoje",
        allowed_action_ids=["any-action"],
        repository=repository,
    )

    assert answer is not None
    assert "factory-status" in answer.lower()
    assert "api-delpi" in answer


def test_gap_answer_when_factory_status_not_enabled_on_agent():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "factory-status",
            "operationId": "get_product_factory_status",
            "path": "/products/{code}/factory-status",
            "method": "GET",
        }
    ]

    answer = ChatPlaybookProductActionReadinessService.resolve_gap_direct_answer(
        "status fabril do produto 90269002 hoje",
        allowed_action_ids=["execute-sql"],
        repository=repository,
    )

    assert answer is not None
    assert "habilitada" in answer.lower()
    assert "factory-status" in answer


def test_no_gap_when_factory_status_enabled():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "factory-status",
            "operationId": "get_product_factory_status",
            "path": "/products/{code}/factory-status",
            "method": "GET",
        }
    ]

    answer = ChatPlaybookProductActionReadinessService.resolve_gap_direct_answer(
        "status fabril do produto 90269002 hoje",
        allowed_action_ids=["factory-status"],
        repository=repository,
    )

    assert answer is None
