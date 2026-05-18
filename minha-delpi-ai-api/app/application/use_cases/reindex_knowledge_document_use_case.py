from uuid import UUID

from app.application.services.knowledge_ingestion_pipeline_service import (
    KnowledgeIngestionPipelineService,
)
from app.domain.exceptions.knowledge_exceptions import (
    InvalidKnowledgeDocumentInputError,
    KnowledgeDocumentNotFoundError,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class ReindexKnowledgeDocumentUseCase:
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

    def execute(self, document_id: str, user_id: str) -> dict:
        document_uuid = UUID(document_id)
        document = self.knowledge_repository.get_document_by_id(document_uuid)

        if not document:
            raise KnowledgeDocumentNotFoundError()

        prepared = self.pipeline.prepare(
            document.content,
            title=document.title,
            source_type=document.source_type,
            source_ref=document.source_ref,
            document_metadata=document.metadata,
        )

        if not prepared.chunks:
            raise InvalidKnowledgeDocumentInputError(
                "content did not generate indexable chunks"
            )

        document_metadata = dict(document.metadata or {})
        document_metadata.update(
            {
                "contentHash": prepared.content_hash,
                "wordCount": prepared.word_count,
                "ingestionPipeline": prepared.stats,
            }
        )

        updated = self.knowledge_repository.update_document(
            document_uuid,
            content=prepared.cleaned_content,
            metadata=document_metadata,
        )

        if updated:
            document = updated

        self.knowledge_repository.delete_chunks_by_document_id(document_uuid)

        for index, chunk in enumerate(prepared.chunks):
            embedding = self.embedding_gateway.embed(chunk.content)

            chunk_metadata = {
                **chunk.metadata,
                "reindexed": True,
            }

            self.knowledge_repository.create_chunk(
                document_id=document_uuid,
                chunk_index=index,
                content=chunk.content,
                embedding=embedding,
                metadata=chunk_metadata,
            )

        if self.audit_repository:
            self.audit_repository.log(
                user_id=UUID(user_id),
                action="chat.knowledge.document.reindexed",
                context="admin",
                metadata={
                    "document_id": str(document.id),
                    "title": document.title,
                    "source_ref": document.source_ref,
                    "chunks": len(prepared.chunks),
                    "pipeline": prepared.stats,
                },
            )

        return {
            "id": str(document.id),
            "title": document.title,
            "chunks": len(prepared.chunks),
            "active": document.active,
            "pipeline": prepared.stats,
        }
