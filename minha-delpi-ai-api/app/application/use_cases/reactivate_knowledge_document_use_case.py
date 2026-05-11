from uuid import UUID

from app.domain.exceptions.knowledge_exceptions import KnowledgeDocumentNotFoundError
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class ReactivateKnowledgeDocumentUseCase:
    def __init__(
        self,
        knowledge_repository: KnowledgeRepositoryPort,
        audit_repository: AuditRepositoryPort,
    ):
        self.knowledge_repository = knowledge_repository
        self.audit_repository = audit_repository

    def execute(self, document_id: str, user_id: str) -> dict:
        document = self.knowledge_repository.reactivate_document(UUID(document_id))

        if not document:
            raise KnowledgeDocumentNotFoundError()

        self.audit_repository.log(
            user_id=UUID(user_id),
            action="chat.knowledge.document.reactivated",
            context="admin",
            metadata={
                "document_id": str(document.id),
                "title": document.title,
                "source_ref": document.source_ref,
            },
        )

        return {
            "id": str(document.id),
            "title": document.title,
            "active": document.active,
            "updatedAt": document.updated_at.isoformat(),
        }
