from app.application.services.chat_learning_capture_service import (
    ChatLearningCaptureService,
)
from app.infrastructure.config.settings import Settings


class FakeCandidateService:
    def __init__(self):
        self.registered: list[dict] = []

    def register_candidate(self, candidate, *, created_by=None):
        self.registered.append(candidate)
        return {"id": len(self.registered), "status": "pending", **candidate}


def test_capture_from_feedback_disabled_by_flag(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", False)
    fake = FakeCandidateService()
    service = ChatLearningCaptureService(candidate_service=fake)

    result = service.capture_from_negative_feedback(user_question="como vc s chama?")

    assert result is None
    assert fake.registered == []


def test_capture_from_feedback_detects_explicit_definition(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_CAPTURE_FROM_FEEDBACK", True)
    fake = FakeCandidateService()
    service = ChatLearningCaptureService(candidate_service=fake)

    result = service.capture_from_negative_feedback(
        user_question="lousa significa o canvas do chat",
        reason="did_not_understand",
    )

    assert result is not None
    assert len(fake.registered) == 1
    assert fake.registered[0]["candidateType"] == "term_definition"


def test_capture_from_feedback_builds_normalization_candidate(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_CAPTURE_FROM_FEEDBACK", True)
    fake = FakeCandidateService()
    service = ChatLearningCaptureService(candidate_service=fake)

    service.capture_from_negative_feedback(
        user_question="como vc s chama?",
        reason="did_not_understand",
    )

    assert len(fake.registered) == 1
    assert fake.registered[0]["candidateType"] == "normalization_rule"
    # Motivo de "não entendeu" eleva a confiança base.
    assert fake.registered[0]["confidence"] == 0.5


def test_capture_from_turn_disabled_by_flag(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", False)
    fake = FakeCandidateService()
    service = ChatLearningCaptureService(candidate_service=fake)

    result = service.capture_explicit_definition_from_turn(
        message="quando eu falar X, é Y qualquer",
    )

    assert result is None
    assert fake.registered == []
