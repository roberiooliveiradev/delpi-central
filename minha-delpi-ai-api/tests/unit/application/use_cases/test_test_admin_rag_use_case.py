import pytest
from uuid import uuid4

from app.application.use_cases.admin_rag_test_use_case import AdminRagTestUseCase


class FakeChunk:
    def __init__(self, score=0.9):
        self.id = uuid4()
        self.document_id = uuid4()
        self.chunk_index = 0
        self.content = "Diretriz global de teste para atendimento."
        self.metadata = {}
        self.created_at = None
        self.score = score
        self.title = "Diretrizes"
        self.source_type = "diretriz"
        self.source_ref = "global:diretrizes"


class FakeKnowledgeRepository:
    def __init__(self):
        self.filters = None

    def search_similar_chunks(self, embedding, limit, filters=None):
        self.filters = filters
        return [FakeChunk()]

    def search_keyword_chunks(self, query, limit, filters=None):
        return []


class FakeEmbeddingGateway:
    def embed(self, text):
        return [0.1, 0.2, 0.3]


def test_admin_rag_test_searches_global_scope():
    repository = FakeKnowledgeRepository()

    result = AdminRagTestUseCase(
        knowledge_repository=repository,
        embedding_gateway=FakeEmbeddingGateway(),
    ).execute(question="Como o chat deve responder?")

    assert repository.filters == {"include_global": True}
    assert result["score"] == 0.9
    assert result["matchedDocuments"][0]["title"] == "Diretrizes"
    assert result["chunks"][0]["preview"]


def test_admin_rag_test_rejects_empty_question():
    with pytest.raises(ValueError, match="question is required"):
        AdminRagTestUseCase(
            knowledge_repository=FakeKnowledgeRepository(),
            embedding_gateway=FakeEmbeddingGateway(),
        ).execute(question="   ")



class FakeGuidelineRepository:
    def list_active(self, *, environment=None):
        return [
            {
                "id": "guideline-1",
                "title": "Não inventar respostas",
                "category": "behavior",
                "status": "active",
                "description": "Se não houver fonte suficiente, admita limitação.",
            }
        ]


def test_admin_rag_test_returns_applied_guidelines():
    use_case = AdminRagTestUseCase(
        knowledge_repository=FakeKnowledgeRepository(),
        embedding_gateway=FakeEmbeddingGateway(),
        guideline_repository=FakeGuidelineRepository(),
    )

    result = use_case.execute(question="Quem sou eu?")

    assert result["appliedGuidelines"] == [
        {
            "id": "guideline-1",
            "title": "Não inventar respostas",
            "category": "behavior",
            "status": "active",
            "description": "Se não houver fonte suficiente, admita limitação.",
        }
    ]
    assert result["triggeredGuidelines"] == result["appliedGuidelines"]
    assert result["debugContext"]["guidelineCount"] == 1
    assert result["debugContext"]["hasActiveGuidelines"] is True
    assert "Não inventar respostas" in result["debugContext"]["safeContextPreview"]
    assert result["comparison"]["withGuidelines"]["guidelineCount"] == 1
    assert result["comparison"]["withoutGuidelines"]["guidelineCount"] == 0
    assert result["comparison"]["withoutRag"]["chunkCount"] == 0
