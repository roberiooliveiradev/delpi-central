import pytest

from app.application.services.chat_error_handling_service import ChatErrorHandlingService
from app.domain.services.chat_error_handling_classifier import ChatErrorHandlingClassifier
from tests.fixtures.error_empty_states_cases import ERROR_EMPTY_STATES_CASES


def _case(case_id: str) -> dict:
    for item in ERROR_EMPTY_STATES_CASES:
        if item["id"] == case_id:
            return item

    raise KeyError(case_id)


@pytest.mark.parametrize("case", ERROR_EMPTY_STATES_CASES, ids=lambda c: c["id"])
def test_error_cases_classify_and_attach(case):
    metadata: dict = {}

    classification = ChatErrorHandlingClassifier.classify(
        message=case["message"],
        answer=case["answer"],
        tool_calls=case.get("tool_calls"),
        attachments=case.get("attachments"),
    )

    assert classification is not None
    assert classification.error_type == case["expect_type"]

    ChatErrorHandlingService.attach_to_assistant_metadata(
        metadata,
        message=case["message"],
        answer=case["answer"],
        tool_calls=case.get("tool_calls"),
        attachments=case.get("attachments"),
    )

    handling = metadata.get("errorHandling") or {}

    assert handling.get("type") == case["expect_type"]
    assert handling.get("userMessage")
    assert metadata.get("errorRecoveryFollowUpSuggestions")

    if case.get("expect_api_failed"):
        assert handling.get("apiFailed") is True

    if case.get("expect_non_existence_flag") is False:
        assert handling.get("affirmsNonExistence") is False

    if case.get("expect_enriched"):
        assert metadata.get("errorHandlingEnrichedAnswer")


def test_e13_api_failure_must_not_mark_non_existence():
    case = _case("E13")
    metadata: dict = {}

    ChatErrorHandlingService.attach_to_assistant_metadata(
        metadata,
        message=case["message"],
        answer=case["answer"],
        tool_calls=case["tool_calls"],
    )

    assert metadata["errorHandling"]["apiFailed"] is True
    assert metadata["errorHandling"]["affirmsNonExistence"] is False


def test_structured_answer_includes_reasons():
    case = _case("E1")
    classification = ChatErrorHandlingClassifier.classify(
        message=case["message"],
        answer=case["answer"],
        tool_calls=case["tool_calls"],
    )

    assert classification
    config = ChatErrorHandlingService.type_config(classification.error_type)
    text = ChatErrorHandlingService.build_structured_answer(classification, config=config)

    assert "Possíveis motivos" in text
    assert "Não encontrei registros" in text


def test_help_error_skipped_when_recovery_present():
    from app.application.services.chat_help_error_follow_up_service import (
        ChatHelpErrorFollowUpService,
    )

    metadata = {
        "errorRecoveryFollowUpSuggestions": [{"label": "Tentar novamente", "query": "x"}],
    }

    ChatHelpErrorFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="x",
        answer="erro",
        issues=["failed"],
    )

    assert "helpErrorFollowUpSuggestions" not in metadata
