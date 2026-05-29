from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.rag_context_service import RagContextService


class FakeSearchKnowledgeUseCase:
    def __init__(self, chunks):
        self.chunks = chunks
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.chunks


def _rag_service(chunks: list) -> RagContextService:
    service = RagContextService(FakeSearchKnowledgeUseCase(chunks))
    service.intelligence_settings_service = type(
        "S",
        (),
        {"resolve": lambda self: type("R", (), {"rag_context_min_score": 0.35})()},
    )()
    return service


def test_build_context_includes_scope_metadata_in_sources():
    service = _rag_service(
        [
            {
                    "id": "chunk-1",
                    "documentId": "doc-1",
                    "title": "Documento",
                    "sourceType": "chat_attachment",
                    "sourceRef": "attachment-1",
                    "chunkIndex": 0,
                    "content": "Conteúdo relevante",
                    "score": 0.98,
                    "metadata": {
                        "scope": "session_source",
                        "userId": "user-1",
                        "sessionId": "session-1",
                        "projectId": "project-1",
                        "agentKey": "agent-1",
                        "attachmentId": "attachment-1",
                        "originalFilename": "manual.md",
                        "contentType": "text/markdown",
                    },
                }
        ]
    )

    result = service.build_context(
        "pergunta",
        filters={
            "user_id": "user-1",
            "session_id": "session-1",
        },
        min_score=0.35,
    )

    assert "Conteúdo relevante" in result["context"]
    assert "Escopo: session_source" in result["context"]
    assert "Arquivo: manual.md" in result["context"]

    assert result["sources"] == [
        {
            "id": "chunk-1",
            "documentId": "doc-1",
            "title": "Documento",
            "sourceType": "chat_attachment",
            "sourceRef": "attachment-1",
            "chunkIndex": 0,
            "score": 0.98,
            "scope": "session_source",
            "userId": "user-1",
            "sessionId": "session-1",
            "projectId": "project-1",
            "agentKey": "agent-1",
            "attachmentId": "attachment-1",
            "originalFilename": "manual.md",
            "contentType": "text/markdown",
            "chunks": [0],
        }
    ]


def test_build_context_limits_chunks_per_document_and_deduplicates_sources():
    service = _rag_service(
        [
                {
                    "id": "chunk-1",
                    "documentId": "doc-1",
                    "title": "Documento SQL",
                    "sourceType": "agent_source",
                    "sourceRef": "arquivo.txt",
                    "chunkIndex": 1,
                    "content": "Trecho 1 SELECT * FROM X",
                    "score": 0.50,
                    "metadata": {"scope": "agent_source"},
                },
                {
                    "id": "chunk-2",
                    "documentId": "doc-1",
                    "title": "Documento SQL",
                    "sourceType": "agent_source",
                    "sourceRef": "arquivo.txt",
                    "chunkIndex": 2,
                    "content": "Trecho 2 SELECT * FROM Y",
                    "score": 0.60,
                    "metadata": {"scope": "agent_source"},
                },
                {
                    "id": "chunk-3",
                    "documentId": "doc-1",
                    "title": "Documento SQL",
                    "sourceType": "agent_source",
                    "sourceRef": "arquivo.txt",
                    "chunkIndex": 3,
                    "content": "Trecho 3 SELECT * FROM Z",
                    "score": 0.99,
                    "metadata": {"scope": "agent_source"},
                },
        ]
    )

    result = service.build_context("produto 10080014", min_score=0.35)

    assert "Trecho 1" in result["context"]
    assert "Trecho 2" in result["context"]
    assert "Trecho 3" not in result["context"]

    # Fontes do agente entram no contexto do LLM, mas não na lista exibida ao usuário.
    assert result["sources"] == []


def test_build_context_returns_empty_sources_when_no_chunks():
    service = _rag_service([])

    result = service.build_context("pergunta", min_score=0.35)

    assert result == {
        "context": "",
        "sources": [],
    }


def test_build_context_filters_chunks_below_min_score():
    service = _rag_service(
        [
                {
                    "id": "chunk-low",
                    "documentId": "doc-1",
                    "title": "Baixo",
                    "sourceType": "global",
                    "sourceRef": "ref",
                    "chunkIndex": 0,
                    "content": "Trecho irrelevante",
                    "score": 0.20,
                    "metadata": {"scope": "global"},
                },
                {
                    "id": "chunk-high",
                    "documentId": "doc-2",
                    "title": "Alto",
                    "sourceType": "global",
                    "sourceRef": "ref",
                    "chunkIndex": 0,
                    "content": "Trecho relevante",
                    "score": 0.80,
                    "metadata": {"scope": "global"},
                },
        ]
    )

    result = service.build_context("pergunta", min_score=0.35)

    assert "Trecho relevante" in result["context"]
    assert "Trecho irrelevante" not in result["context"]
    # Fontes globais entram no contexto do LLM, mas não na lista exibida ao usuário.
    assert result["sources"] == []


def test_build_context_applies_chunk_filter():
    service = _rag_service(
        [
            {
                "id": "normas",
                "documentId": "doc-n",
                "title": "Normas_Tecnicas_DELPI.md",
                "sourceType": "admin_upload",
                "sourceRef": "admin_upload:Normas_Tecnicas_DELPI.md",
                "chunkIndex": 0,
                "content": "## 1009 · Isoladores",
                "score": 0.9,
                "metadata": {
                    "scope": "global",
                    "originalFilename": "Normas_Tecnicas_DELPI.md",
                },
            },
            {
                "id": "chat-doc",
                "documentId": "doc-c",
                "title": "O_ARQUITETO_DO_CODIGO.md",
                "sourceType": "admin_upload",
                "sourceRef": "admin_upload:O_ARQUITETO_DO_CODIGO.md",
                "chunkIndex": 0,
                "content": "Assistente Minha DELPI Chat com RAG.",
                "score": 0.85,
                "metadata": {
                    "scope": "global",
                    "originalFilename": "O_ARQUITETO_DO_CODIGO.md",
                },
            },
        ]
    )

    result = service.build_context(
        "quem te criou?",
        min_score=0.1,
        chunk_filter=ChatAssistantIdentityService.identity_chunk_filter(),
    )

    assert "Isoladores" not in result["context"]
    assert "Minha DELPI" in result["context"]
