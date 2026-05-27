import pytest

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_external_action_direct_answer_service import (
    ChatExternalActionDirectAnswerService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from tests.fixtures.chat_intelligence_regression_cases import (
    ANALYSIS_INTENT_CASES,
    DIRECT_ANSWER_CASES,
    INTENT_CASES,
    OPERATIONAL_FAST_PATH_CASES,
    PRODUCT_CODE_CASES,
    SELECTION_CASES,
)


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return self.actions


@pytest.mark.parametrize("message,expected_intent", INTENT_CASES)
def test_intent_regression(message, expected_intent):
    assert ChatProductQueryIntentService.detect(message) == expected_intent


@pytest.mark.parametrize("case", PRODUCT_CODE_CASES)
def test_product_code_regression(case):
    if len(case) == 2:
        message, expected = case
        context = None
    else:
        message, expected, context = case

    assert ChatProductQueryIntentService.resolve_product_code(message, context) == expected


@pytest.mark.parametrize("message,expected", ANALYSIS_INTENT_CASES)
def test_analysis_intent_regression(message, expected):
    assert (
        ChatAnalysisIntentService.is_comparison_or_insight_request(message) is expected
    )


@pytest.mark.parametrize("message,expected", OPERATIONAL_FAST_PATH_CASES)
def test_operational_fast_path_regression(message, expected):
    assert (
        ChatOperationalPipelineService.should_optimize(
            message,
            ["action-1"],
        )
        is expected
    )


@pytest.mark.parametrize("case", SELECTION_CASES)
def test_action_selection_regression(case):
    service = ExternalActionSelectionService(FakeRepository(case["actions"]))
    allowed = [action["actionId"] for action in case["actions"]]

    selected = service.select_action(case["message"], allowed_action_ids=allowed)

    assert selected is not None
    assert selected["arguments"]["actionId"] == case["expected_action_id"]

    expected_parameters = case.get("expected_parameters")

    if expected_parameters:
        params = selected["arguments"].get("parameters") or {}

        for key, value in expected_parameters.items():
            assert params.get(key) == value


@pytest.mark.parametrize("case", DIRECT_ANSWER_CASES)
def test_direct_answer_regression(case):
    answer = ChatExternalActionDirectAnswerService.format(
        case["humanized"],
        message=case["message"],
        path=case["path"],
        operation_id=case["operation_id"],
    )

    assert answer is not None

    for token in case["must_contain"]:
        assert token in answer
