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
        }
    ]


def test_build_context_returns_empty_sources_when_no_chunks():
    service = RagContextService(FakeSearchKnowledgeUseCase([]))

    result = service.build_context("pergunta")

    assert result == {
        "context": "",
        "sources": [],
    }
