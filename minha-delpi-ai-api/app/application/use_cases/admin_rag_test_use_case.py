from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class AdminRagTestUseCase:
    def __init__(
        self,
        *,
        knowledge_repository: KnowledgeRepositoryPort,
        embedding_gateway: EmbeddingGatewayPort,
        guideline_repository=None,
    ):
        self.knowledge_repository = knowledge_repository
        self.embedding_gateway = embedding_gateway
        self.guideline_repository = guideline_repository

    def execute(
        self,
        *,
        question: str,
        document_id: str | None = None,
        limit: int = 5,
    ) -> dict:
        normalized_question = str(question or "").strip()

        if not normalized_question:
            raise ValueError("question is required")

        safe_limit = max(1, min(int(limit or 5), 10))
        embedding = self.embedding_gateway.embed(normalized_question)

        filters: dict = {
            "include_global": True,
        }

        if document_id:
            filters["document_id"] = str(document_id)

        chunks = self.knowledge_repository.search_similar_chunks(
            embedding=embedding,
            limit=safe_limit,
            filters=filters,
        )

        matched_documents_by_id: dict[str, dict] = {}
        chunk_results = []

        for chunk in chunks:
            document_key = str(chunk.document_id)
            score = float(chunk.score or 0)

            chunk_results.append(
                {
                    "id": str(chunk.id),
                    "documentId": document_key,
                    "title": chunk.title,
                    "sourceType": chunk.source_type,
                    "sourceRef": chunk.source_ref,
                    "chunkIndex": chunk.chunk_index,
                    "score": score,
                    "preview": chunk.content[:700],
                }
            )

            current_document = matched_documents_by_id.get(document_key)

            if not current_document or score > current_document["score"]:
                matched_documents_by_id[document_key] = {
                    "id": document_key,
                    "title": chunk.title,
                    "score": score,
                    "sourceType": chunk.source_type,
                    "sourceRef": chunk.source_ref,
                }

        matched_documents = sorted(
            matched_documents_by_id.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        top_score = matched_documents[0]["score"] if matched_documents else 0
        applied_guidelines = self._list_applied_guidelines()

        return {
            "question": normalized_question,
            "score": top_score,
            "answerPreview": self._build_answer_preview(chunks),
            "matchedDocuments": matched_documents,
            "chunks": chunk_results,
            "triggeredGuidelines": applied_guidelines,
            "appliedGuidelines": applied_guidelines,
        }

    def _build_answer_preview(self, chunks) -> str:
        if not chunks:
            return (
                "Nenhum trecho relevante foi encontrado na base global de conhecimento."
            )

        previews = []

        for index, chunk in enumerate(chunks[:3], start=1):
            title = chunk.title or "Documento sem título"
            content = " ".join(str(chunk.content or "").split())
            previews.append(f"{index}. {title}: {content[:280]}")

        return "\n".join(previews)


    def _list_applied_guidelines(self) -> list[dict]:
        if not self.guideline_repository:
            return []

        guidelines = self.guideline_repository.list_active()

        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
                "description": item.get("description"),
            }
            for item in guidelines
        ]
