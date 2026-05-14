from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.infrastructure.config.settings import Settings


class RagContextService:
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
        sources: list[dict] = []
        total_chars = 0

        for index, chunk in enumerate(chunks, start=1):
            content = chunk.get("content") or ""

            if not content:
                continue

            remaining = Settings.MAX_CONTEXT_CHARS - total_chars

            if remaining <= 0:
                break

            clipped_content = content[:remaining]
            total_chars += len(clipped_content)

            label = f"[Fonte {index}]"

            context_parts.append(
                "\n".join(
                    [
                        label,
                        f"Título: {chunk.get('title') or 'Documento sem título'}",
                        f"Origem: {chunk.get('sourceRef') or chunk.get('sourceType') or 'desconhecida'}",
                        f"Trecho: {clipped_content}",
                    ]
                )
            )

            sources.append(self._source_from_chunk(chunk))

        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
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
