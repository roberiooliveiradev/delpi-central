from app.application.services.chat_glossary_retrieval_service import (
    ChatGlossaryRetrievalService,
)
from app.infrastructure.config.settings import Settings


class _FakeVocabRepo:
    def __init__(self, definitions):
        self._definitions = definitions

    def list_active_definitions(self, **kwargs):
        return self._definitions


_DEFS = [
    {"term": "PKCE", "normalizedTerm": "pkce", "meaning": "Extensão do OAuth2.", "scope": "global"},
    {"term": "RAG", "normalizedTerm": "rag", "meaning": "Geração aumentada por recuperação.", "scope": "global"},
]


def test_match_definitions_finds_term_in_message():
    loaded = [
        {"term": "PKCE", "matchable": "pkce", "meaning": "Extensão do OAuth2."},
        {"term": "RAG", "matchable": "rag", "meaning": "Geração aumentada."},
    ]

    matches = ChatGlossaryRetrievalService.match_definitions("como funciona o PKCE aqui?", loaded)

    assert len(matches) == 1
    assert matches[0]["term"] == "PKCE"


def test_match_definitions_word_boundary():
    loaded = [{"term": "RAG", "matchable": "rag", "meaning": "..."}]
    # "fragmento" contém "rag" mas não como palavra inteira
    assert ChatGlossaryRetrievalService.match_definitions("um fragmento qualquer", loaded) == []


def test_build_block_renders_terms():
    block = ChatGlossaryRetrievalService.build_block(
        [{"term": "PKCE", "meaning": "Extensão do OAuth2."}]
    )
    assert "Glossário" in block
    assert "PKCE: Extensão do OAuth2." in block


def test_build_block_empty():
    assert ChatGlossaryRetrievalService.build_block([]) == ""


def test_build_context_block_gated(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", False, raising=False)
    service = ChatGlossaryRetrievalService(vocabulary_repository=_FakeVocabRepo(_DEFS))
    assert service.build_context_block_for(message="o que é PKCE?") == ""


def test_build_context_block_when_enabled(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_RETRIEVAL", True, raising=False)

    service = ChatGlossaryRetrievalService(vocabulary_repository=_FakeVocabRepo(_DEFS))
    service.refresh()

    block = service.build_context_block_for(message="me explica PKCE por favor")

    assert "PKCE: Extensão do OAuth2." in block
    assert "RAG" not in block
