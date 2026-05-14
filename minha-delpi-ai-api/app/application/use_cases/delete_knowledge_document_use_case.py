from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class DeleteKnowledgeDocumentUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        audit_repository: AuditRepositoryPort | None = None,
    ):
        self.knowledge_repository = knowledge_repository
        self.audit_repository = audit_repository

    def execute(self, *, document_id: str, user_id: str) -> dict:
        document_uuid = UUID(document_id)
        document = self.knowledge_repository.get_document_by_id(document_uuid)

        if not document:
            raise ValueError("knowledge document not found")

        self.knowledge_repository.delete_document(document_uuid)

        if self.audit_repository:
            self.audit_repository.log(
                user_id=UUID(user_id),
                action="chat.knowledge.document.deleted",
                context="admin",
                metadata={
                    "document_id": str(document.id),
                    "title": document.title,
                    "source_type": document.source_type,
                    "source_ref": document.source_ref,
                },
            )

        return {
            "id": str(document.id),
            "title": document.title,
            "deleted": True,
        }
