from uuid import UUID

from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.domain.exceptions.knowledge_exceptions import InvalidKnowledgeDocumentInputError
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.infrastructure.config.settings import Settings


class IngestKnowledgeDocumentUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
        pipeline: KnowledgeIngestionPipelineService | None = None,
        audit_repository: AuditRepositoryPort | None = None,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway
        self.pipeline = pipeline or KnowledgeIngestionPipelineService()
        self.audit_repository = audit_repository

    def execute(self, request: IngestDocumentRequest) -> dict:
        title = self._validate_title(request.title)
        source_type = self._validate_source_type(request.source_type)
        source_ref = self._validate_source_ref(request.source_ref)
        content = self._validate_content(request.content)

        prepared = self.pipeline.prepare(
            content,
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            document_metadata=request.metadata,
        )

        if not prepared.chunks:
            raise InvalidKnowledgeDocumentInputError(
                "content did not generate indexable chunks"
            )

        duplicate = None

        if Settings.KNOWLEDGE_PIPELINE_ENABLED and prepared.content_hash:
            duplicate = self.knowledge_repository.find_global_document_by_content_hash(
                prepared.content_hash,
                source_ref=source_ref,
            )

        if duplicate:
            self._audit_ingestion(
                request=request,
                document_id=str(duplicate.id),
                title=duplicate.title,
                source_type=source_type,
                source_ref=source_ref,
                chunks=0,
                skipped_duplicate=True,
                pipeline_stats=prepared.stats,
            )

            return {
                "id": str(duplicate.id),
                "title": duplicate.title,
                "chunks": 0,
                "duplicate": True,
                "skipped": True,
                "pipeline": prepared.stats,
            }

        document_metadata = dict(request.metadata or {})
        document_metadata.update(
            {
                "contentHash": prepared.content_hash,
                "wordCount": prepared.word_count,
                "ingestionPipeline": prepared.stats,
            }
        )

        document = self.knowledge_repository.create_document(
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            content=prepared.cleaned_content,
            metadata=document_metadata,
        )

        for index, chunk in enumerate(prepared.chunks):
            embedding = self.embedding_gateway.embed(chunk.content)

            self.knowledge_repository.create_chunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk.content,
                embedding=embedding,
                metadata=chunk.metadata,
            )

        self._audit_ingestion(
            request=request,
            document_id=str(document.id),
            title=document.title,
            source_type=source_type,
            source_ref=source_ref,
            chunks=len(prepared.chunks),
            skipped_duplicate=False,
            pipeline_stats=prepared.stats,
        )

        return {
            "id": str(document.id),
            "title": document.title,
            "chunks": len(prepared.chunks),
            "duplicate": False,
            "skipped": False,
            "pipeline": prepared.stats,
        }

    def _audit_ingestion(
        self,
        request: IngestDocumentRequest,
        document_id: str,
        title: str,
        source_type: str,
        source_ref: str | None,
        chunks: int,
        *,
        skipped_duplicate: bool,
        pipeline_stats: dict,
    ) -> None:
        if not self.audit_repository or not request.user_id:
            return

        self.audit_repository.log(
            user_id=UUID(request.user_id),
            action="chat.knowledge.document.ingested",
            context="admin",
            metadata={
                "document_id": document_id,
                "title": title,
                "source_type": source_type,
                "source_ref": source_ref,
                "chunks": chunks,
                "skipped_duplicate": skipped_duplicate,
                "pipeline": pipeline_stats,
            },
        )

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
