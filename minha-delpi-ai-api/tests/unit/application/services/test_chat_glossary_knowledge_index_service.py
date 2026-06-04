import uuid

from app.application.services.chat_glossary_knowledge_index_service import (
    ChatGlossaryKnowledgeIndexService,
)
from app.infrastructure.config.settings import Settings


class _Doc:
    def __init__(self, doc_id, metadata):
        self.id = doc_id
        self.metadata = metadata


class _FakeKnowledgeRepo:
    def __init__(self, existing=None):
        self.existing = existing
        self.created_docs = []
        self.created_chunks = []
        self.updated = []
        self.deleted_chunks = []
        self.deleted_docs = []

    def find_document_by_source_ref(self, source_ref, *, source_type=None):
        return self.existing

    def create_document(self, *, title, source_type, source_ref, content, metadata=None):
        doc = _Doc(uuid.uuid4(), metadata)
        self.created_docs.append(
            {"title": title, "source_type": source_type, "source_ref": source_ref,
             "content": content, "metadata": metadata}
        )
        return doc

    def create_chunk(self, *, document_id, chunk_index, content, embedding, metadata=None):
        self.created_chunks.append(
            {"document_id": document_id, "chunk_index": chunk_index,
             "content": content, "embedding": embedding, "metadata": metadata}
        )
        return None

    def update_document(self, document_id, *, content=None, metadata=None):
        self.updated.append({"id": document_id, "content": content, "metadata": metadata})
        return None

    def delete_chunks_by_document_id(self, document_id):
        self.deleted_chunks.append(document_id)

    def delete_document(self, document_id):
        self.deleted_docs.append(document_id)


class _FakeEmbedder:
    def embed(self, text):
        return [0.1, 0.2, 0.3]


def _enable(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_RAG_INDEX", True, raising=False)


def _service(repo, embedder=None):
    return ChatGlossaryKnowledgeIndexService(
        knowledge_repository=repo,
        embedding_gateway=embedder or _FakeEmbedder(),
    )


def _term(**overrides):
    base = {
        "id": 42,
        "term": "Onda 13",
        "meaning": "Fase de visão documental.",
        "type": "term_definition",
        "projectId": None,
        "active": True,
        "approved": True,
    }
    base.update(overrides)
    return base


def test_disabled_flag_returns_none(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_GLOSSARY_RAG_INDEX", False, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    repo = _FakeKnowledgeRepo()
    assert _service(repo).index_term(_term()) is None
    assert repo.created_docs == []


def test_index_new_term_creates_document_and_chunk(monkeypatch):
    _enable(monkeypatch)
    repo = _FakeKnowledgeRepo(existing=None)

    result = _service(repo).index_term(_term())

    assert result and result.get("created") is True
    assert len(repo.created_docs) == 1
    doc = repo.created_docs[0]
    assert doc["source_type"] == "glossary"
    assert doc["source_ref"] == "glossary:42"
    assert "Onda 13" in doc["content"] and "documental" in doc["content"]
    assert doc["metadata"]["scope"] == "global"
    assert doc["metadata"]["vocabularyTermId"] == 42
    assert len(repo.created_chunks) == 1
    assert repo.created_chunks[0]["embedding"] == [0.1, 0.2, 0.3]


def test_index_skips_when_hash_unchanged(monkeypatch):
    _enable(monkeypatch)
    service = ChatGlossaryKnowledgeIndexService()
    content = service.build_content("Onda 13", "Fase de visão documental.")
    content_hash = ChatGlossaryKnowledgeIndexService._hash(content)
    existing = _Doc(uuid.uuid4(), {"contentHash": content_hash})
    repo = _FakeKnowledgeRepo(existing=existing)

    result = _service(repo).index_term(_term())

    assert result and result.get("skipped") is True
    assert repo.created_docs == []
    assert repo.updated == []


def test_index_reindexes_when_meaning_changes(monkeypatch):
    _enable(monkeypatch)
    existing = _Doc(uuid.uuid4(), {"contentHash": "stale"})
    repo = _FakeKnowledgeRepo(existing=existing)

    result = _service(repo).index_term(_term(meaning="Novo significado."))

    assert result and result.get("reindexed") is True
    assert len(repo.updated) == 1
    assert repo.deleted_chunks == [existing.id]
    assert len(repo.created_chunks) == 1


def test_project_scope_metadata(monkeypatch):
    _enable(monkeypatch)
    repo = _FakeKnowledgeRepo(existing=None)
    project_id = str(uuid.uuid4())

    _service(repo).index_term(_term(projectId=project_id))

    meta = repo.created_docs[0]["metadata"]
    assert meta["scope"] == "project_source"
    assert meta["projectId"] == project_id


def test_sync_inactive_term_deindexes(monkeypatch):
    _enable(monkeypatch)
    existing = _Doc(uuid.uuid4(), {"contentHash": "x"})
    repo = _FakeKnowledgeRepo(existing=existing)

    result = _service(repo).sync_term(_term(active=False))

    assert result is None
    assert repo.deleted_docs == [existing.id]


def test_sync_ignores_non_definition(monkeypatch):
    _enable(monkeypatch)
    repo = _FakeKnowledgeRepo()
    assert _service(repo).sync_term(_term(type="typo")) is None
    assert repo.created_docs == []
    assert repo.deleted_docs == []


def test_deindex_missing_document_returns_false(monkeypatch):
    _enable(monkeypatch)
    repo = _FakeKnowledgeRepo(existing=None)
    assert _service(repo).deindex_term(99) is False


def test_reindex_all_counts(monkeypatch):
    _enable(monkeypatch)
    repo = _FakeKnowledgeRepo(existing=None)
    terms = [_term(id=1), _term(id=2, type="typo"), _term(id=3, active=False)]

    summary = _service(repo).reindex_all(terms)

    assert summary["enabled"] is True
    assert summary["processed"] == 3
    assert summary["indexed"] == 1
