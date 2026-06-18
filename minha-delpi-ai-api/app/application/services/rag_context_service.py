import logging
from collections.abc import Callable

from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.services.chat_source_visibility_service import filter_client_visible_sources
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.rag")


class RagContextService:
    MAX_CHUNKS_PER_DOCUMENT = 2

    def __init__(
        self,
        search_knowledge_use_case: SearchKnowledgeUseCase,
        intelligence_settings_service=None,
    ):
        self.search_knowledge_use_case = search_knowledge_use_case
        if intelligence_settings_service is None:
            from app.application.services.chat_intelligence_settings_service import (
                ChatIntelligenceSettingsService,
            )

            intelligence_settings_service = ChatIntelligenceSettingsService()

        self.intelligence_settings_service = intelligence_settings_service

    def build_context(
        self,
        query: str,
        filters: dict | None = None,
        *,
        min_score: float | None = None,
        chunk_filter: Callable[[dict], bool] | None = None,
    ) -> dict:
        chunks = self.search_knowledge_use_case.execute(
            SearchKnowledgeRequest(
                query=query,
                limit=Settings.MAX_CONTEXT_CHUNKS,
                filters=filters,
            )
        )

        if not chunks:
            return {
                "context": "",
                "sources": [],
                "retrievedSourceCount": 0,
                "visibleSourceCount": 0,
                "retrievedChunkCount": 0,
            }

        if min_score is None:
            min_score = self.intelligence_settings_service.resolve().rag_context_min_score
        filtered_chunks = [
            chunk
            for chunk in chunks
            if chunk.get("score") is None or float(chunk["score"]) >= min_score
        ]

        if len(filtered_chunks) < len(chunks):
            logger.debug(
                "RAG chunks filtered by min score %.2f: %s -> %s",
                min_score,
                len(chunks),
                len(filtered_chunks),
            )

        if not filtered_chunks:
            return {
                "context": "",
                "sources": [],
                "retrievedSourceCount": 0,
                "visibleSourceCount": 0,
                "retrievedChunkCount": 0,
            }

        if chunk_filter is not None:
            before = len(filtered_chunks)
            filtered_chunks = [chunk for chunk in filtered_chunks if chunk_filter(chunk)]
            if before != len(filtered_chunks):
                logger.debug(
                    "RAG chunks filtered by custom predicate: %s -> %s",
                    before,
                    len(filtered_chunks),
                )

        if not filtered_chunks:
            return {
                "context": "",
                "sources": [],
                "retrievedSourceCount": 0,
                "visibleSourceCount": 0,
                "retrievedChunkCount": 0,
            }

        chunks = filtered_chunks

        context_parts: list[str] = []
        sources_by_document: dict[str, dict] = {}
        chunks_by_document: dict[str, int] = {}
        total_chars = 0
        source_index = 0

        for chunk in chunks:
            content = chunk.get("content") or ""

            if not content:
                continue

            document_key = str(chunk.get("documentId") or chunk.get("id") or "")
            if not document_key:
                continue

            used_count = chunks_by_document.get(document_key, 0)
            if used_count >= self.MAX_CHUNKS_PER_DOCUMENT:
                continue

            remaining = Settings.MAX_CONTEXT_CHARS - total_chars

            if remaining <= 0:
                break

            clipped_content = content[:remaining]
            total_chars += len(clipped_content)
            chunks_by_document[document_key] = used_count + 1
            source_index += 1

            label = f"[Fonte {source_index}]"

            metadata = chunk.get("metadata") or {}
            scope = metadata.get("scope") or chunk.get("sourceType")

            context_parts.append(
                "\n".join(
                    [
                        label,
                        f"Título: {chunk.get('title') or 'Documento sem título'}",
                        f"Origem: {chunk.get('sourceRef') or chunk.get('sourceType') or 'desconhecida'}",
                        f"Escopo: {scope or 'desconhecido'}",
                        f"Arquivo: {metadata.get('originalFilename') or chunk.get('title') or 'não informado'}",
                        f"Trecho: {clipped_content}",
                    ]
                )
            )

            source = self._source_from_chunk(chunk)
            existing = sources_by_document.get(document_key)

            if not existing:
                source["chunks"] = [chunk.get("chunkIndex")]
                sources_by_document[document_key] = source
            else:
                existing.setdefault("chunks", []).append(chunk.get("chunkIndex"))
                existing["score"] = max(
                    value
                    for value in [existing.get("score"), chunk.get("score")]
                    if value is not None
                ) if any(value is not None for value in [existing.get("score"), chunk.get("score")]) else None

        sources = filter_client_visible_sources(list(sources_by_document.values()))

        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "retrievedSourceCount": len(sources_by_document),
            "visibleSourceCount": len(sources),
            "retrievedChunkCount": source_index,
        }

    def _source_from_chunk(self, chunk: dict) -> dict:
        metadata = chunk.get("metadata") or {}
        source_type = chunk.get("sourceType")
        scope = metadata.get("scope")

        if not scope and source_type in {
            "project_source",
            "agent_source",
            "chat_attachment",
        }:
            scope = source_type if source_type != "chat_attachment" else "session_source"

        return {
            "id": chunk.get("id"),
            "documentId": chunk.get("documentId"),
            "title": chunk.get("title"),
            "sourceType": source_type,
            "sourceRef": chunk.get("sourceRef"),
            "chunkIndex": chunk.get("chunkIndex"),
            "score": chunk.get("score"),
            "scope": scope,
            "userId": metadata.get("userId"),
            "sessionId": metadata.get("sessionId"),
            "projectId": metadata.get("projectId"),
            "agentId": metadata.get("agentId"),
            "attachmentId": metadata.get("attachmentId"),
            "originalFilename": metadata.get("originalFilename"),
            "contentType": metadata.get("contentType"),
        }
