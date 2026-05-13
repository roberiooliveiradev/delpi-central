from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.use_cases.chat_sources_use_cases import DeleteChatSourceUseCase


@dataclass(frozen=True)
class FakeDocument:
    id: object
    title: str
    source_type: str
    source_ref: str | None
    content: str
    metadata: dict
    active: bool
    created_at: object
    updated_at: object


class FakeKnowledgeRepository:
    def __init__(self, document):
        self.document = document
        self.deactivated = False

    def get_document_by_id(self, document_id):
        return self.document

    def deactivate_document(self, document_id):
        self.deactivated = True
        return self.document


class FakeProjectRepository:
    def __init__(self, role):
        self.role = role

    def get_accessible_by_id(self, project_id, user_id):
        return object(), self.role


def test_delete_project_source_requires_editor_or_owner():
    user_id = str(uuid4())
    source_id = str(uuid4())
    project_id = str(uuid4())

    document = FakeDocument(
        id=source_id,
        title="Fonte",
        source_type="project_source",
        source_ref=None,
        content="conteúdo",
        metadata={
            "scope": "project_source",
            "projectId": project_id,
            "userId": user_id,
        },
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    knowledge_repository = FakeKnowledgeRepository(document)

    use_case = DeleteChatSourceUseCase(
        knowledge_repository=knowledge_repository,
        project_repository=FakeProjectRepository(role="viewer"),
    )

    assert use_case.execute(user_id=user_id, source_id=source_id) is False
    assert knowledge_repository.deactivated is False

    use_case = DeleteChatSourceUseCase(
        knowledge_repository=knowledge_repository,
        project_repository=FakeProjectRepository(role="editor"),
    )

    assert use_case.execute(user_id=user_id, source_id=source_id) is True
