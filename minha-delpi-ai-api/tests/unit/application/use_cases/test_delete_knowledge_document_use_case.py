from uuid import uuid4

import pytest

from app.application.use_cases.delete_knowledge_document_use_case import (
    DeleteKnowledgeDocumentUseCase,
)


class FakeDocument:
    def __init__(self):
        self.id = uuid4()
        self.title = "Manual"
        self.source_type = "manual"
        self.source_ref = "manual:test"


class FakeRepository:
    def __init__(self, document):
        self.document = document
        self.deleted_id = None

    def get_document_by_id(self, document_id):
        return self.document

    def delete_document(self, document_id):
        self.deleted_id = document_id


class FakeAuditRepository:
    def __init__(self):
        self.logs = []

    def log(self, **kwargs):
        self.logs.append(kwargs)


def test_delete_knowledge_document_deletes_and_audits():
    document = FakeDocument()
    repository = FakeRepository(document)
    audit_repository = FakeAuditRepository()

    result = DeleteKnowledgeDocumentUseCase(
        knowledge_repository=repository,
        audit_repository=audit_repository,
    ).execute(document_id=str(document.id), user_id=str(uuid4()))

    assert result == {
        "id": str(document.id),
        "title": "Manual",
        "deleted": True,
    }
    assert repository.deleted_id == document.id
    assert audit_repository.logs[0]["action"] == "chat.knowledge.document.deleted"


def test_delete_knowledge_document_raises_when_missing():
    repository = FakeRepository(None)

    with pytest.raises(ValueError, match="not found"):
        DeleteKnowledgeDocumentUseCase(repository).execute(
            document_id=str(uuid4()),
            user_id=str(uuid4()),
        )
