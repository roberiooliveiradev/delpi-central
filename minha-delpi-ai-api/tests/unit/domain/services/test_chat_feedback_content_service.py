import pytest

from app.domain.services.chat_feedback_content_service import ChatFeedbackContentService


def test_normalize_reason_accepts_known_id():
    assert ChatFeedbackContentService.normalize_reason("wrong_data") == "wrong_data"


def test_normalize_reason_rejects_unknown():
    with pytest.raises(ValueError):
        ChatFeedbackContentService.normalize_reason("invalid_reason")


def test_thanks_for_positive_rating():
    message = ChatFeedbackContentService.thanks_for_rating(1, seed="msg-1")

    assert message
    assert len(message) > 5
