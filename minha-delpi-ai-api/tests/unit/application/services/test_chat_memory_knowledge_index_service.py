import uuid

from app.application.services.chat_memory_knowledge_index_service import (
    ChatMemoryKnowledgeIndexService,
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
        self.deleted_docs = []

    def find_document_by_source_ref(self, source_ref, *, source_type=None):
        return self.existing

    def create_document(self, *, title, source_type, source_ref, content, metadata=None):
        doc = _Doc(uuid.uuid4(), metadata)
        self.created_docs.append(
            {
                "title": title,
                "source_type": source_type,
                "source_ref": source_ref,
                "content": content,
            }
        )
        return doc

    def create_chunk(self, *, document_id, chunk_index, content, embedding, metadata=None):
        self.created_chunks.append({"content": content, "embedding": embedding})
        return None

    def update_document(self, document_id, *, content=None, metadata=None):
        return None

    def delete_chunks_by_document_id(self, document_id):
        return None

    def delete_document(self, document_id):
        self.deleted_docs.append(document_id)


class _FakeEmbedder:
    def embed(self, text):
        return [0.1, 0.2, 0.3]


def _service(repo=None, embedder=None):
    return ChatMemoryKnowledgeIndexService(
        knowledge_repository=repo or _FakeKnowledgeRepo(),
        embedding_gateway=embedder or _FakeEmbedder(),
    )


def test_index_active_memory_item(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_RAG_INDEX", True)

    repo = _FakeKnowledgeRepo()
    result = _service(repo).index_item(
        {
            "id": 7,
            "userId": "11111111-1111-4111-8111-111111111111",
            "type": "preference",
            "content": "Prefiro respostas curtas",
            "status": "active",
        }
    )

    assert result is not None
    assert result.get("created") is True
    assert repo.created_docs[0]["source_type"] == "user_memory"
    assert repo.created_docs[0]["source_ref"] == "memory:7"
    assert repo.created_chunks[0]["embedding"] == [0.1, 0.2, 0.3]


def test_deindex_forgotten_memory(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_RAG_INDEX", True)

    existing = _Doc(uuid.uuid4(), {"contentHash": "x"})
    repo = _FakeKnowledgeRepo(existing=existing)

    _service(repo).sync_item(
        {
            "id": 9,
            "userId": "11111111-1111-4111-8111-111111111111",
            "content": "x",
            "status": "forgotten",
        }
    )

    assert len(repo.deleted_docs) == 1
