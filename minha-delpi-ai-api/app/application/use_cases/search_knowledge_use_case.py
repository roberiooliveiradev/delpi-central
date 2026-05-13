from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.infrastructure.config.settings import Settings


class SearchKnowledgeUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway

    def execute(self, request: SearchKnowledgeRequest) -> list[dict]:
        query = request.query.strip()

        if not query:
            return []

        limit = max(1, min(request.limit, Settings.MAX_CONTEXT_CHUNKS))

        embedding = self.embedding_gateway.embed(query)

        chunks = self.knowledge_repository.search_similar_chunks(
            embedding=embedding,
            limit=limit,
            filters=request.filters,
        )

        return [
            {
                "id": str(chunk.id),
                "documentId": str(chunk.document_id),
                "title": chunk.title,
                "sourceType": chunk.source_type,
                "sourceRef": chunk.source_ref,
                "chunkIndex": chunk.chunk_index,
                "content": chunk.content,
                "score": chunk.score,
            }
            for chunk in chunks
        ]
