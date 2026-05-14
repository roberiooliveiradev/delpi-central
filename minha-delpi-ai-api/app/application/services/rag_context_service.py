from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.infrastructure.config.settings import Settings


class RagContextService:
    MAX_CHUNKS_PER_DOCUMENT = 2

    def __init__(self, search_knowledge_use_case: SearchKnowledgeUseCase):
        self.search_knowledge_use_case = search_knowledge_use_case

    def build_context(self, query: str, filters: dict | None = None) -> dict:
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
            }

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

            context_parts.append(
                "\n".join(
                    [
                        label,
                        f"Título: {chunk.get('title') or 'Documento sem título'}",
                        f"Origem: {chunk.get('sourceRef') or chunk.get('sourceType') or 'desconhecida'}",
                        f"Escopo: {metadata.get('scope') or 'desconhecido'}",
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

        return {
            "context": "\n\n".join(context_parts),
            "sources": list(sources_by_document.values()),
        }

    def _source_from_chunk(self, chunk: dict) -> dict:
        metadata = chunk.get("metadata") or {}

        return {
            "id": chunk.get("id"),
            "documentId": chunk.get("documentId"),
            "title": chunk.get("title"),
            "sourceType": chunk.get("sourceType"),
            "sourceRef": chunk.get("sourceRef"),
            "chunkIndex": chunk.get("chunkIndex"),
            "score": chunk.get("score"),
            "scope": metadata.get("scope"),
            "userId": metadata.get("userId"),
            "sessionId": metadata.get("sessionId"),
            "projectId": metadata.get("projectId"),
            "agentKey": metadata.get("agentKey"),
            "attachmentId": metadata.get("attachmentId"),
            "originalFilename": metadata.get("originalFilename"),
            "contentType": metadata.get("contentType"),
        }
