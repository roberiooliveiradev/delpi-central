from app.application.services.rag_context_service import RagContextService


class FakeSearchKnowledgeUseCase:
    def __init__(self, chunks):
        self.chunks = chunks
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.chunks


def test_build_context_includes_scope_metadata_in_sources():
    service = RagContextService(
        FakeSearchKnowledgeUseCase(
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
    )

    result = service.build_context(
        "pergunta",
        filters={
            "user_id": "user-1",
            "session_id": "session-1",
        },
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
    service = RagContextService(
        FakeSearchKnowledgeUseCase(
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
    )

    result = service.build_context("produto 10080014")

    assert "Trecho 1" in result["context"]
    assert "Trecho 2" in result["context"]
    assert "Trecho 3" not in result["context"]

    assert len(result["sources"]) == 1
    assert result["sources"][0]["documentId"] == "doc-1"
    assert result["sources"][0]["chunks"] == [1, 2]
    assert result["sources"][0]["score"] == 0.60


def test_build_context_returns_empty_sources_when_no_chunks():
    service = RagContextService(FakeSearchKnowledgeUseCase([]))

    result = service.build_context("pergunta")

    assert result == {
        "context": "",
        "sources": [],
    }


def test_build_context_filters_chunks_below_min_score():
    service = RagContextService(
        FakeSearchKnowledgeUseCase(
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
    )

    result = service.build_context("pergunta")

    assert "Trecho relevante" in result["context"]
    assert "Trecho irrelevante" not in result["context"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["documentId"] == "doc-2"
