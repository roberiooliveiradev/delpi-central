from uuid import uuid4
from datetime import datetime, timezone

from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.entities.knowledge_chunk import KnowledgeChunk


class FakeRepository:
    def search_similar_chunks(self, embedding, limit, filters=None):
        return [
            KnowledgeChunk(
                id=uuid4(),
                document_id=uuid4(),
                chunk_index=0,
                content="texto genérico sobre processos",
                metadata={},
                created_at=datetime.now(timezone.utc),
                score=0.9,
                title="A",
                source_type="global",
                source_ref="a",
            )
        ]

    def search_keyword_chunks(self, query, limit, filters=None, *, use_fts=True):
        return [
            KnowledgeChunk(
                id=uuid4(),
                document_id=uuid4(),
                chunk_index=0,
                content="pedidos abertos do cliente na fila",
                metadata={},
                created_at=datetime.now(timezone.utc),
                score=0.4,
                title="B",
                source_type="global",
                source_ref="b",
            )
        ]


class FakeEmbedding:
    def embed(self, text):
        return [0.1, 0.2]


def test_hybrid_search_rerank_promotes_keyword_match(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.search_knowledge_use_case.Settings.CHAT_RAG_HYBRID_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.application.use_cases.search_knowledge_use_case.Settings.CHAT_RAG_RERANK_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.application.use_cases.search_knowledge_use_case.Settings.MAX_CONTEXT_CHUNKS",
        1,
    )

    use_case = SearchKnowledgeUseCase(FakeRepository(), FakeEmbedding())
    results = use_case.execute(
        SearchKnowledgeRequest(query="pedidos abertos", limit=1, filters={}),
    )

    assert len(results) == 1
    assert "pedidos" in results[0]["content"]
