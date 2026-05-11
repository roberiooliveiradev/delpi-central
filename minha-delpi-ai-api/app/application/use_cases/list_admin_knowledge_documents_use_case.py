from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class ListAdminKnowledgeDocumentsUseCase:
    def __init__(self, knowledge_repository: KnowledgeRepositoryPort):
        self.knowledge_repository = knowledge_repository

    def execute(self, limit: int = 100) -> list[dict]:
        safe_limit = max(1, min(int(limit), 200))
        documents = self.knowledge_repository.list_documents(limit=safe_limit)

        return [
            {
                "id": str(document.id),
                "title": document.title,
                "sourceType": document.source_type,
                "sourceRef": document.source_ref,
                "active": document.active,
                "metadata": document.metadata,
                "createdAt": document.created_at.isoformat(),
                "updatedAt": document.updated_at.isoformat(),
            }
            for document in documents
        ]
