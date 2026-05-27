import pytest

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError


class FakeKnowledgeRepository:
    def __init__(self):
        self.duplicate = None

    def find_global_document_by_content_hash(self, content_hash, source_ref=None):
        return self.duplicate

    def create_document(self, title, source_type, source_ref, content, metadata=None):
        class Document:
            id = "00000000-0000-0000-0000-000000000001"

        document = Document()
        document.title = title
        return document

    def create_chunk(self, document_id, chunk_index, content, embedding, metadata=None):
        return None


class FakeEmbeddingGateway:
    def embed(self, text):
        return [0.1, 0.2, 0.3]


class FakePipeline:
    def prepare(self, content, **kwargs):
        class Result:
            cleaned_content = content
            content_hash = "hash-test"
            word_count = len(content.split())
            chunks = [type("Chunk", (), {"content": content, "metadata": {}})()]
            stats = {
                "chunkStrategy": "single",
                "chunksAfterDedup": 1,
                "duplicatesRemoved": 0,
            }

        return Result()


class FakeAuditRepository:
    def __init__(self):
        self.logs = []

    def log(self, **kwargs):
        self.logs.append(kwargs)

    def list_logs_page(self, query):
        return self.logs[: query.limit], len(self.logs)

    def get_log(self, log_id):
        return None

    def list_by_prompt_hash(self, **kwargs):
        return []

    def list_logs(self, limit=100):
        return self.logs[:limit]


def make_use_case(audit_repository=None, knowledge_repository=None):
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=knowledge_repository or FakeKnowledgeRepository(),
        embedding_gateway=FakeEmbeddingGateway(),
        pipeline=FakePipeline(),
        audit_repository=audit_repository,
    )


def test_ingests_valid_document():
    use_case = make_use_case()

    result = use_case.execute(
        IngestDocumentRequest(
            title="Documento Teste",
            source_type="manual",
            source_ref="test:doc",
            content="Conteúdo válido.",
        )
    )

    assert result["title"] == "Documento Teste"
    assert result["chunks"] == 1


def test_audits_ingestion_when_user_id_is_available():
    audit_repository = FakeAuditRepository()
    use_case = make_use_case(audit_repository=audit_repository)

    use_case.execute(
        IngestDocumentRequest(
            title="Documento Teste",
            source_type="manual",
            source_ref="test:doc",
            content="Conteúdo válido.",
            user_id="00000000-0000-0000-0000-000000000099",
        )
    )

    assert audit_repository.logs[0]["action"] == "chat.knowledge.document.ingested"
    assert audit_repository.logs[0]["metadata"]["chunks"] == 1


def test_rejects_empty_title():
    use_case = make_use_case()

    with pytest.raises(InvalidKnowledgeDocumentInputError):
        use_case.execute(
            IngestDocumentRequest(
                title="",
                source_type="manual",
                source_ref=None,
                content="Conteúdo válido.",
            )
        )


def test_rejects_empty_content():
    use_case = make_use_case()

    with pytest.raises(InvalidKnowledgeDocumentInputError):
        use_case.execute(
            IngestDocumentRequest(
                title="Documento Teste",
                source_type="manual",
                source_ref=None,
                content="",
            )
        )


def test_ingests_document_above_legacy_50k_limit(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.ingest_knowledge_document_use_case.Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS",
        2_000_000,
    )
    use_case = make_use_case()
    content = "x" * 60_000

    result = use_case.execute(
        IngestDocumentRequest(
            title="Documento grande",
            source_type="manual",
            source_ref="test:large",
            content=content,
        )
    )

    assert result["title"] == "Documento grande"
    assert result["chunks"] == 1


def test_rejects_document_above_configured_max_chars(monkeypatch):
    monkeypatch.setattr(
        "app.application.use_cases.ingest_knowledge_document_use_case.Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS",
        1_000,
    )
    use_case = make_use_case()

    with pytest.raises(InvalidKnowledgeDocumentInputError, match="content exceeds 1000 characters"):
        use_case.execute(
            IngestDocumentRequest(
                title="Documento grande",
                source_type="manual",
                source_ref=None,
                content="a" * 1_001,
            )
        )
