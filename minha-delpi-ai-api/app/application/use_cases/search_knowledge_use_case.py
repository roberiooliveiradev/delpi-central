from dataclasses import replace

from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.domain.services.keyword_similarity import keyword_overlap_score
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.infrastructure.config.settings import Settings


class SearchKnowledgeUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
        intelligence_settings_service: ChatIntelligenceSettingsService | None = None,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway
        self.intelligence_settings_service = (
            intelligence_settings_service or ChatIntelligenceSettingsService()
        )

    def execute(self, request: SearchKnowledgeRequest) -> list[dict]:
        query = request.query.strip()

        if not query:
            return []

        limit = max(1, min(request.limit, Settings.MAX_CONTEXT_CHUNKS))
        filters = request.filters

        if self._hybrid_enabled():
            chunks = self._hybrid_search(query, limit=limit, filters=filters)
        elif (
            self.intelligence_settings_service.resolve().rag_prefer_keyword_search
            and self._fts_enabled()
        ):
            chunks = self.knowledge_repository.search_keyword_chunks(
                query,
                limit=limit,
                filters=filters,
                use_fts=True,
            )
        else:
            chunks = self._vector_search(query, limit=limit, filters=filters)

        chunks = self._rerank_chunks(query, chunks, limit=limit, filters=filters)

        return [self._chunk_to_dict(chunk) for chunk in chunks]

    @staticmethod
    def _scope_priority_boost(chunk, filters: dict | None) -> float:
        priority = str((filters or {}).get("scope_priority") or "").strip()

        if not priority:
            return 0.0

        source_type = str(getattr(chunk, "source_type", None) or "").strip()

        if source_type == priority:
            return Settings.CHAT_RAG_SCOPE_PRIORITY_BOOST

        metadata = getattr(chunk, "metadata", None) or {}

        if isinstance(metadata, dict):
            scope = str(metadata.get("scope") or "").strip()

            if scope == priority:
                return Settings.CHAT_RAG_SCOPE_PRIORITY_BOOST

        return 0.0

    def _rerank_chunks(
        self,
        query: str,
        chunks: list,
        *,
        limit: int,
        filters: dict | None = None,
    ) -> list:
        if not self._rerank_enabled() or not chunks:
            return chunks

        boost = Settings.CHAT_RAG_RERANK_KEYWORD_BOOST

        def score_chunk(chunk) -> float:
            base = float(chunk.score or 0)
            overlap = keyword_overlap_score(query, chunk.content or "")
            return base + boost * overlap + self._scope_priority_boost(chunk, filters)

        return sorted(chunks, key=score_chunk, reverse=True)[:limit]

    def _hybrid_enabled(self) -> bool:
        return self.intelligence_settings_service.resolve().rag_hybrid_enabled

    def _rerank_enabled(self) -> bool:
        return self.intelligence_settings_service.resolve().rag_rerank_enabled

    def _fts_enabled(self) -> bool:
        return self.intelligence_settings_service.resolve().rag_fts_enabled

    def _vector_search(self, query: str, *, limit: int, filters: dict | None) -> list:
        candidate_limit = limit

        if self._hybrid_enabled():
            candidate_limit = limit * Settings.CHAT_RAG_HYBRID_CANDIDATE_MULTIPLIER

        embedding = self.embedding_gateway.embed(query)

        return self.knowledge_repository.search_similar_chunks(
            embedding=embedding,
            limit=candidate_limit,
            filters=filters,
        )

    def _hybrid_search(self, query: str, *, limit: int, filters: dict | None) -> list:
        candidate_limit = limit * Settings.CHAT_RAG_HYBRID_CANDIDATE_MULTIPLIER

        vector_chunks = self._vector_search(query, limit=candidate_limit, filters=filters)
        keyword_chunks = self.knowledge_repository.search_keyword_chunks(
            query,
            limit=candidate_limit,
            filters=filters,
            use_fts=self._fts_enabled(),
        )

        merged: dict[str, object] = {}

        for chunk in vector_chunks:
            key = str(chunk.id)
            vector_score = float(chunk.score or 0)
            merged[key] = {
                "chunk": chunk,
                "vector_score": vector_score,
                "keyword_score": 0.0,
            }

        for chunk in keyword_chunks:
            key = str(chunk.id)
            keyword_score = float(chunk.score or 0)
            existing = merged.get(key)

            if existing:
                existing["keyword_score"] = max(float(existing["keyword_score"]), keyword_score)
            else:
                merged[key] = {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "keyword_score": keyword_score,
                }

        vector_weight = Settings.CHAT_RAG_HYBRID_VECTOR_WEIGHT
        keyword_weight = Settings.CHAT_RAG_HYBRID_KEYWORD_WEIGHT

        ranked = sorted(
            merged.values(),
            key=lambda item: (
                vector_weight * float(item["vector_score"])
                + keyword_weight * float(item["keyword_score"])
            ),
            reverse=True,
        )

        result = []

        for item in ranked[:limit]:
            chunk = item["chunk"]
            combined = (
                vector_weight * float(item["vector_score"])
                + keyword_weight * float(item["keyword_score"])
            )
            result.append(replace(chunk, score=combined))

        return result

    def _chunk_to_dict(self, chunk) -> dict:
        return {
            "id": str(chunk.id),
            "documentId": str(chunk.document_id),
            "title": chunk.title,
            "sourceType": chunk.source_type,
            "sourceRef": chunk.source_ref,
            "chunkIndex": chunk.chunk_index,
            "content": chunk.content,
            "score": chunk.score,
            "metadata": dict(chunk.metadata or {}),
        }
