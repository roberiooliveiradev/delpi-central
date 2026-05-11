from uuid import UUID

from app.domain.exceptions.chat_exceptions import ChatSessionNotFoundError
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.services.text_chunker_service import TextChunkerService


class ReindexKnowledgeDocumentUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
        chunker: TextChunkerService,
        audit_repository: AuditRepositoryPort,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway
        self.chunker = chunker
        self.audit_repository = audit_repository

    def execute(self, document_id: str, user_id: str) -> dict:
        document_uuid = UUID(document_id)
        document = self.knowledge_repository.get_document_by_id(document_uuid)

        if not document:
            raise ChatSessionNotFoundError()

        chunks = self.chunker.chunk(document.content)

        self.knowledge_repository.delete_chunks_by_document_id(document_uuid)

        for index, chunk in enumerate(chunks):
            embedding = self.embedding_gateway.embed(chunk)

            self.knowledge_repository.create_chunk(
                document_id=document_uuid,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                metadata={
                    "title": document.title,
                    "source_type": document.source_type,
                    "source_ref": document.source_ref,
                    "reindexed": True,
                },
            )

        self.audit_repository.log(
            user_id=UUID(user_id),
            action="chat.knowledge.document.reindexed",
            context="admin",
            metadata={
                "document_id": str(document.id),
                "title": document.title,
                "source_ref": document.source_ref,
                "chunks": len(chunks),
            },
        )

        return {
            "id": str(document.id),
            "title": document.title,
            "chunks": len(chunks),
            "active": document.active,
        }
