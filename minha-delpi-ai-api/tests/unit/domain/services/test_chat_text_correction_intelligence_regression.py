"""Regressão — correção de texto (playbook C1–C12, intent e pipeline)."""

import pytest

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_preference_service import (
    ChatTextCorrectionPreferenceService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from tests.fixtures.chat_intelligence_regression_cases import (
    TEXT_CORRECTION_MODE_CASES,
    TEXT_CORRECTION_PREFERENCE_DETECT_CASES,
    TEXT_CORRECTION_PURE_TEXT_TASK_CASES,
    TEXT_CORRECTION_SOURCE_CASES,
    TEXT_CORRECTION_SUBTYPE_CASES,
)


@pytest.mark.parametrize("message,expected_subtype", TEXT_CORRECTION_SUBTYPE_CASES)
def test_text_correction_subtype_regression(message, expected_subtype):
    assert ChatTextCorrectionIntentService.classify_subtype(message) == expected_subtype


@pytest.mark.parametrize("message,expected", TEXT_CORRECTION_MODE_CASES)
def test_text_correction_mode_regression(message, expected):
    assert ChatTextCorrectionIntentService.is_text_correction(message) is expected


@pytest.mark.parametrize("message,expected_pure", TEXT_CORRECTION_PURE_TEXT_TASK_CASES)
def test_text_correction_pure_text_task_regression(message, expected_pure):
    assert ChatTextTaskIntentService.is_pure_text_task(message) is expected_pure


@pytest.mark.parametrize("message,expected_flags", TEXT_CORRECTION_PREFERENCE_DETECT_CASES)
def test_text_correction_preference_detect_regression(message, expected_flags):
    prefs = ChatTextCorrectionPreferenceService.detect(message)

    for key, value in expected_flags.items():
        assert prefs.get(key) is value


@pytest.mark.parametrize("message,expected_source", TEXT_CORRECTION_SOURCE_CASES)
def test_text_correction_source_regression(message, expected_source):
    ctx = ChatTextCorrectionIntentService.extract_context(message)
    assert ctx.get("source") == expected_source
