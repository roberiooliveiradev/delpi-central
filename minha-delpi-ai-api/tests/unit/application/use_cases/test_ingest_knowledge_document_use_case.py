import pytest

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.use_cases.ingest_knowledge_document_use_case import (
    IngestKnowledgeDocumentUseCase,
)
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError


class FakeKnowledgeRepository:
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


class FakeChunker:
    def chunk(self, text):
        return [text]


def make_use_case():
    return IngestKnowledgeDocumentUseCase(
        knowledge_repository=FakeKnowledgeRepository(),
        embedding_gateway=FakeEmbeddingGateway(),
        chunker=FakeChunker(),
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
