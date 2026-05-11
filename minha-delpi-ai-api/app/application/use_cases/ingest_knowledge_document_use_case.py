from app.application.dto.ingest_document_request import IngestDocumentRequest
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.domain.services.text_chunker_service import TextChunkerService


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
        title = request.title.strip()
        source_type = request.source_type.strip()
        content = request.content.strip()

        if not title:
            raise ValueError("title is required")

        if not source_type:
            raise ValueError("source_type is required")

        if not content:
            raise ValueError("content is required")

        document = self.knowledge_repository.create_document(
            title=title,
            source_type=source_type,
            source_ref=request.source_ref,
            content=content,
            metadata=request.metadata,
        )

        chunks = self.chunker.chunk(content)

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
                    "source_ref": request.source_ref,
                },
            )

        return {
            "id": str(document.id),
            "title": document.title,
            "chunks": len(chunks),
        }
