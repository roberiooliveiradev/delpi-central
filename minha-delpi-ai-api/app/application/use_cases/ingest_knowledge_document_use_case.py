from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.services.text_chunker_service import TextChunkerService
from app.infrastructure.config.settings import Settings


class IngestKnowledgeDocumentUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
        chunker: TextChunkerService,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway
        self.chunker = chunker

    def execute(self, request: IngestDocumentRequest) -> dict:
        title = self._validate_title(request.title)
        source_type = self._validate_source_type(request.source_type)
        source_ref = self._validate_source_ref(request.source_ref)
        content = self._validate_content(request.content)

        document = self.knowledge_repository.create_document(
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            content=content,
            metadata=request.metadata,
        )

        chunks = self.chunker.chunk(content)

        if not chunks:
            raise InvalidKnowledgeDocumentInputError(
                "content did not generate indexable chunks"
            )

        for index, chunk in enumerate(chunks):
            embedding = self.embedding_gateway.embed(chunk)

            self.knowledge_repository.create_chunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                metadata={
                    "title": title,
                    "source_type": source_type,
                    "source_ref": source_ref,
                },
            )

        return {
            "id": str(document.id),
            "title": document.title,
            "chunks": len(chunks),
        }

    def _validate_title(self, value: str) -> str:
        title = str(value or "").strip()

        if not title:
            raise InvalidKnowledgeDocumentInputError("title is required")

        if len(title) > Settings.KNOWLEDGE_TITLE_MAX_CHARS:
            raise InvalidKnowledgeDocumentInputError(
                f"title exceeds {Settings.KNOWLEDGE_TITLE_MAX_CHARS} characters"
            )

        return title

    def _validate_source_type(self, value: str) -> str:
        source_type = str(value or "").strip()

        if not source_type:
            raise InvalidKnowledgeDocumentInputError("sourceType is required")

        if len(source_type) > 50:
            raise InvalidKnowledgeDocumentInputError("sourceType exceeds 50 characters")

        return source_type

    def _validate_source_ref(self, value: str | None) -> str | None:
        if value is None:
            return None

        source_ref = str(value).strip()

        if not source_ref:
            return None

        if len(source_ref) > Settings.KNOWLEDGE_SOURCE_REF_MAX_CHARS:
            raise InvalidKnowledgeDocumentInputError(
                f"sourceRef exceeds {Settings.KNOWLEDGE_SOURCE_REF_MAX_CHARS} characters"
            )

        return source_ref

    def _validate_content(self, value: str) -> str:
        content = str(value or "").strip()

        if not content:
            raise InvalidKnowledgeDocumentInputError("content is required")

        if len(content) > Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS:
            raise InvalidKnowledgeDocumentInputError(
                f"content exceeds {Settings.KNOWLEDGE_DOCUMENT_MAX_CHARS} characters"
            )

        return content
