"""Filtro de chunks RAG para perguntas de identidade do assistente."""

import pytest

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.rag_context_service import RagContextService


def _normas_chunk() -> dict:
    return {
        "id": "c1",
        "documentId": "d1",
        "title": "Normas_Tecnicas_DELPI.md",
        "content": "## 1009 · Isoladores\nTERM. LUVA 2,00-4,00MM2 ROHS",
        "score": 0.45,
        "metadata": {"originalFilename": "Normas_Tecnicas_DELPI.md", "scope": "global"},
    }


def _arquiteto_chunk() -> dict:
    return {
        "id": "c2",
        "documentId": "d2",
        "title": "O_ARQUITETO_DO_CODIGO.md",
        "content": "O assistente Minha DELPI Chat usa RAG e modelo de linguagem.",
        "score": 0.4,
        "metadata": {"originalFilename": "O_ARQUITETO_DO_CODIGO.md", "scope": "global"},
    }


def test_normas_tecnicas_filename_rejected_even_with_delpi_in_content():
    chunk = _normas_chunk()
    chunk["content"] = "**Fonte:** DELPI\n**Origem:** ENGENHARIA\n## 1012 · Tubo Isolante"
    assert ChatAssistantIdentityService.is_identity_relevant_chunk(chunk) is False


@pytest.mark.parametrize(
    "chunk,expected",
    [
        (_normas_chunk(), False),
        (_arquiteto_chunk(), True),
    ],
)
def test_is_identity_relevant_chunk(chunk: dict, expected: bool):
    assert ChatAssistantIdentityService.is_identity_relevant_chunk(chunk) is expected


def test_build_rag_query_avoids_empresa_documentacao():
    query = ChatAssistantIdentityService.build_rag_query("quem te criou?")
    assert "empresa" not in query.lower()
    assert "Minha DELPI Chat" in query


def test_rag_context_service_applies_chunk_filter():
    search = type("Search", (), {})()
    search.execute = lambda req: [_normas_chunk(), _arquiteto_chunk()]

    service = RagContextService(search_knowledge_use_case=search)
    service.intelligence_settings_service = type(
        "S",
        (),
        {"resolve": lambda self: type("R", (), {"rag_context_min_score": 0.1})()},
    )()

    result = service.build_context(
        "quem te criou?",
        chunk_filter=ChatAssistantIdentityService.identity_chunk_filter(),
        min_score=0.1,
    )

    assert "Isoladores" not in result["context"]
    assert "Minha DELPI" in result["context"] or "assistente" in result["context"].lower()
