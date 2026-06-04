import contextlib

from app.application.services.chat_meaning_discovery_service import (
    ChatMeaningDiscoveryService,
)
from app.infrastructure.config.settings import Settings


class _FakeGlossary:
    def __init__(self, internal=None):
        self._internal = internal

    def lookup_internal(self, term, *, project_id=None):
        return self._internal


class _FakeCandidateService:
    def __init__(self):
        self.registered = []

    def register_candidate(self, candidate, *, created_by=None):
        self.registered.append(candidate)
        return {"id": 1, "status": "pending", **candidate}


class _FakeGateway:
    def __init__(self, payload):
        self.payload = payload
        self.queries = []

    def search(self, query, **kwargs):
        self.queries.append(query)
        return self.payload


@contextlib.contextmanager
def _fake_savepoint():
    yield


def _patch_db(monkeypatch):
    from app.extensions import db as db_module

    class _FakeSession:
        def begin_nested(self):
            return _fake_savepoint()

    monkeypatch.setattr(db_module.db, "session", _FakeSession(), raising=False)


def test_research_web_gated_off(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_WEB_MEANING", False, raising=False)

    service = ChatMeaningDiscoveryService(
        glossary_service=_FakeGlossary(),
        candidate_service=_FakeCandidateService(),
        web_search_gateway=_FakeGateway({"results": []}),
    )

    assert service.research_web_meaning("PKCE") is None


def test_research_web_returns_meaning(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_WEB_MEANING", True, raising=False)

    gateway = _FakeGateway(
        {
            "results": [
                {
                    "title": "PKCE",
                    "snippet": "PKCE é uma extensão do OAuth2.",
                    "url": "https://oauth.net/2/pkce/",
                }
            ]
        }
    )
    service = ChatMeaningDiscoveryService(
        glossary_service=_FakeGlossary(),
        candidate_service=_FakeCandidateService(),
        web_search_gateway=gateway,
    )

    result = service.research_web_meaning("PKCE")

    assert result is not None
    assert "OAuth2" in result["meaning"]
    assert result["sources"] == ["https://oauth.net/2/pkce/"]
    assert gateway.queries == ["o que significa PKCE"]


def test_capture_skips_known_internal_term(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_CAPTURE", True, raising=False)
    _patch_db(monkeypatch)

    candidate_service = _FakeCandidateService()
    service = ChatMeaningDiscoveryService(
        glossary_service=_FakeGlossary(internal={"id": 5, "term": "PKCE"}),
        candidate_service=candidate_service,
    )

    result = service.capture_unknown_term_from_turn(message="o que é PKCE?")

    assert result is None
    assert candidate_service.registered == []


def test_capture_creates_candidate_for_unknown_term(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_CAPTURE", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_WEB_MEANING", False, raising=False)
    _patch_db(monkeypatch)

    candidate_service = _FakeCandidateService()
    service = ChatMeaningDiscoveryService(
        glossary_service=_FakeGlossary(internal=None),
        candidate_service=candidate_service,
    )

    service.capture_unknown_term_from_turn(message="o que significa PKCE?")

    assert len(candidate_service.registered) == 1
    candidate = candidate_service.registered[0]
    assert candidate["candidateType"] == "term_definition"
    assert candidate["term"] == "PKCE"
    assert candidate["source"] == "glossary_unknown_term"


def test_capture_disabled_by_flag(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_CAPTURE", False, raising=False)

    candidate_service = _FakeCandidateService()
    service = ChatMeaningDiscoveryService(
        glossary_service=_FakeGlossary(),
        candidate_service=candidate_service,
    )

    assert service.capture_unknown_term_from_turn(message="o que é PKCE?") is None
    assert candidate_service.registered == []
