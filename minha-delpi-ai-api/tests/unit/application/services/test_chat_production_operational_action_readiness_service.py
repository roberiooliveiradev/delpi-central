from unittest.mock import MagicMock

from app.application.services.chat_production_operational_action_readiness_service import (
    ChatProductionOperationalActionReadinessService,
)


def test_gap_answer_when_route_missing_from_catalog():
    repository = MagicMock()
    repository.list_actions.return_value = []

    answer = ChatProductionOperationalActionReadinessService.resolve_gap_direct_answer(
        "liste produtos programados para produzir hoje na filial 01",
        allowed_action_ids=["any-action"],
        repository=repository,
    )

    assert answer is not None
    assert "schedule" in answer.lower() or "programad" in answer.lower()
    assert "api-delpi" in answer


def test_gap_answer_when_route_not_enabled_on_agent():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "api_delpi.get_production_schedule_today",
            "operationId": "get_production_schedule_today",
            "path": "/production/schedule/today",
            "method": "GET",
        }
    ]

    answer = ChatProductionOperationalActionReadinessService.resolve_gap_direct_answer(
        "liste produtos programados para produzir hoje na filial 01",
        allowed_action_ids=["other-action"],
        repository=repository,
    )

    assert answer is not None
    assert "habilitada" in answer.lower()
    assert "get_production_schedule_today" in answer


def test_no_gap_when_route_enabled():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "api_delpi.get_production_schedule_today",
            "operationId": "get_production_schedule_today",
            "path": "/production/schedule/today",
            "method": "GET",
        }
    ]

    answer = ChatProductionOperationalActionReadinessService.resolve_gap_direct_answer(
        "liste produtos programados para produzir hoje na filial 01",
        allowed_action_ids=["api_delpi.get_production_schedule_today"],
        repository=repository,
    )

    assert answer is None


def test_is_rest_action_ready_when_enabled_on_agent():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "api_delpi.get_production_schedule_today",
            "operationId": "get_production_schedule_today",
            "path": "/production/schedule/today",
            "method": "GET",
        }
    ]

    assert ChatProductionOperationalActionReadinessService.is_rest_action_ready(
        "liste produtos programados para produzir hoje na filial 01",
        allowed_action_ids=["api_delpi.get_production_schedule_today"],
        repository=repository,
    )


def test_is_rest_action_ready_false_when_not_enabled():
    repository = MagicMock()
    repository.list_actions.return_value = [
        {
            "actionId": "api_delpi.get_production_schedule_today",
            "operationId": "get_production_schedule_today",
            "path": "/production/schedule/today",
            "method": "GET",
        }
    ]

    assert not ChatProductionOperationalActionReadinessService.is_rest_action_ready(
        "liste produtos programados para produzir hoje na filial 01",
        allowed_action_ids=["other-action"],
        repository=repository,
    )
