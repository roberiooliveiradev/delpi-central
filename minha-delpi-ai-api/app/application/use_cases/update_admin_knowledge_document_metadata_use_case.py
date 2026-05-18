from uuid import UUID

from app.application.services.knowledge_curatorial_metadata_service import (
    enrich_document_payload,
    merge_curatorial_metadata,
)
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class UpdateAdminKnowledgeDocumentMetadataUseCase:
    def __init__(self, knowledge_repository: KnowledgeRepositoryPort):
        self.knowledge_repository = knowledge_repository

    def execute(
        self,
        *,
        document_id: str,
        category: str | None = None,
        tags: list[str] | str | None = None,
        namespace: str | None = None,
        domain: str | None = None,
        priority: int | float | str | None = None,
        quality_score: int | float | str | None = None,
    ) -> dict:
        document = self.knowledge_repository.get_document_by_id(UUID(str(document_id)))

        if not document:
            raise ValueError("document not found")

        metadata = merge_curatorial_metadata(
            document.metadata,
            category=category,
            tags=tags,
            namespace=namespace,
            domain=domain,
            priority=priority,
            quality_score=quality_score,
        )
        metadata["scope"] = metadata.get("scope") or "global"

        updated = self.knowledge_repository.update_document_metadata(
            UUID(str(document_id)),
            metadata,
        )

        if not updated:
            raise ValueError("document not found")

        return {
            "id": str(updated.id),
            "title": updated.title,
            "metadata": updated.metadata,
            **enrich_document_payload(updated.metadata),
        }
