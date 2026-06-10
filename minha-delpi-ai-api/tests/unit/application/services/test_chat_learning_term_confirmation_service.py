from contextlib import contextmanager
from unittest.mock import Mock, patch

from app.application.services.chat_learning_term_confirmation_service import (
    ChatLearningTermConfirmationService,
)
from app.infrastructure.config.settings import Settings


class _FakeGlossary:
    def lookup_internal(self, term, *, project_id=None):
        return None


class _FakeMeaningDiscovery:
    glossary_service = _FakeGlossary()

    def research_web_meaning(self, term, *, message=None):
        return {
            "meaning": "ordem de produção",
            "sources": ["https://example.com/def"],
        }


def test_build_definition_question_asks_confirmation(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_CAPTURE", True, raising=False)
    monkeypatch.setattr(
        Settings,
        "CHAT_LEARNING_TERM_CONFIRMATION_ENABLED",
        True,
        raising=False,
    )

    service = ChatLearningTermConfirmationService(
        meaning_discovery_service=_FakeMeaningDiscovery(),
        candidate_service=Mock(),
    )

    result = service.try_build(
        message="o que é OP?",
        workspace_context={"workingMemory": {}},
    )

    assert result is not None
    assert "OP" in result["directAnswer"]
    assert result["workingMemoryPatch"]["learningTermConfirmation"]["term"] == "OP"


def test_resolve_pending_confirmation_registers_candidate(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_CAPTURE", True, raising=False)
    monkeypatch.setattr(
        Settings,
        "CHAT_LEARNING_TERM_CONFIRMATION_ENABLED",
        True,
        raising=False,
    )

    candidate_service = Mock()
    candidate_service.register_candidate.return_value = {"id": 1}

    @contextmanager
    def _fake_nested():
        yield

    service = ChatLearningTermConfirmationService(
        meaning_discovery_service=_FakeMeaningDiscovery(),
        candidate_service=candidate_service,
    )

    with patch("app.extensions.db.db.session.begin_nested", _fake_nested):
        result = service.try_build(
        message="sim",
        workspace_context={
            "workingMemory": {
                "learningTermConfirmation": {
                    "term": "OP",
                    "proposedMeaning": "ordem de produção",
                    "confidence": 0.35,
                    "sources": [],
                }
            }
        },
        )

    assert result is not None
    assert "OP" in result["directAnswer"]
    candidate_service.register_candidate.assert_called_once()
