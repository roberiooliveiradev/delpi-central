from uuid import uuid4

from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.entities.knowledge_chunk import KnowledgeChunk


class _FakeIntelligenceSettings:
    def resolve(self):
        return SimpleSettings()


class SimpleSettings:
    rag_hybrid_enabled = False
    rag_prefer_keyword_search = False
    rag_rerank_enabled = True
    rag_fts_enabled = False


def test_rerank_boosts_project_source_when_scope_priority_set():
    use_case = SearchKnowledgeUseCase(
        knowledge_repository=object(),
        embedding_gateway=object(),
        intelligence_settings_service=_FakeIntelligenceSettings(),
    )

    project_chunk = KnowledgeChunk(
        id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        content="cadastrar na minha delpi",
        metadata={"scope": "project_source"},
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        score=0.55,
        title="planilha.xlsx",
        source_type="project_source",
        source_ref="storage/path",
    )
    global_chunk = KnowledgeChunk(
        id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        content="prioridade das fontes globais",
        metadata={"scope": "global"},
        created_at=project_chunk.created_at,
        score=0.60,
        title="GPT_instructions.md",
        source_type="global",
        source_ref="repo:docs",
    )

    ranked = use_case._rerank_chunks(
        "cadastro minha delpi",
        [global_chunk, project_chunk],
        limit=2,
        filters={"scope_priority": "project_source"},
    )

    assert ranked[0].source_type == "project_source"
