"""Regressão — escrita de e-mails (playbook E1–E15, intent e pipeline)."""

import pytest

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_email_preference_service import ChatEmailPreferenceService
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from tests.fixtures.chat_intelligence_regression_cases import (
    EMAIL_PREFERENCE_DETECT_CASES,
    EMAIL_PURE_TEXT_TASK_CASES,
    EMAIL_WRITING_MODE_CASES,
    EMAIL_WRITING_SUBTYPE_CASES,
)


@pytest.mark.parametrize("message,expected_subtype", EMAIL_WRITING_SUBTYPE_CASES)
def test_email_subtype_regression(message, expected_subtype):
    assert ChatEmailIntentService.classify_subtype(message) == expected_subtype


@pytest.mark.parametrize("message,expected_pure", EMAIL_PURE_TEXT_TASK_CASES)
def test_email_pure_text_task_regression(message, expected_pure):
    assert ChatTextTaskIntentService.is_pure_text_task(message) is expected_pure


@pytest.mark.parametrize("message,expected", EMAIL_WRITING_MODE_CASES)
def test_email_writing_mode_regression(message, expected):
    assert ChatEmailIntentService.is_email_writing(message) is expected


@pytest.mark.parametrize("message,expected_flags", EMAIL_PREFERENCE_DETECT_CASES)
def test_email_preference_detect_regression(message, expected_flags):
    prefs = ChatEmailPreferenceService.detect(message)

    for key, value in expected_flags.items():
        assert prefs.get(key) is value
