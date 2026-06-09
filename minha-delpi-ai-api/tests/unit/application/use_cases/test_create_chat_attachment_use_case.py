from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.dto.create_chat_attachment_request import CreateChatAttachmentRequest
from app.application.use_cases.chat_attachments_use_cases import CreateChatAttachmentUseCase
from app.infrastructure.config.settings import Settings


@dataclass
class FakeSession:
    id: object
    user_id: object
    project_id: object | None = None
    agent_id: object | None = None


@dataclass
class FakeAttachment:
    id: object
    user_id: object
    session_id: object
    message_id: object | None
    project_id: object | None
    agent_id: object | None
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    status: str = "uploaded"
    metadata: dict | None = None
    created_at: object = None
    updated_at: object = None


class FakeSessionRepository:
    def get_session_by_id(self, session_id):
        return FakeSession(
            id=session_id,
            user_id=self.user_id,
            project_id=None,
            agent_id=None,
        )

    def __init__(self, user_id):
        self.user_id = user_id


class FakeAttachmentRepository:
    def __init__(self):
        self.created = []
        self.status_updates = []

    def create_attachment(self, **kwargs):
        attachment = FakeAttachment(
            id=uuid4(),
            user_id=kwargs["user_id"],
            session_id=kwargs["session_id"],
            message_id=None,
            project_id=kwargs.get("project_id"),
            agent_id=kwargs.get("agent_id"),
            filename=kwargs["filename"],
            original_filename=kwargs["original_filename"],
            content_type=kwargs["content_type"],
            size_bytes=kwargs["size_bytes"],
            storage_path=kwargs["storage_path"],
            metadata=kwargs.get("metadata"),
        )
        self.created.append(attachment)
        return attachment

    def update_status(self, *, attachment_id, status, metadata):
        self.status_updates.append(
            {
                "attachment_id": attachment_id,
                "status": status,
                "metadata": metadata,
            }
        )

        for attachment in self.created:
            if attachment.id == attachment_id:
                attachment.status = status
                attachment.metadata = metadata
                return attachment

        return None

    def list_attachments_by_ids(self, *, user_id, session_id, attachment_ids):
        return [
            attachment
            for attachment in self.created
            if attachment.id in attachment_ids
        ]


def test_create_attachment_schedules_async_index_without_blocking(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_ATTACHMENT_ASYNC_INDEX", "true")
    Settings.CHAT_ATTACHMENT_ASYNC_INDEX = True

    user_id = uuid4()
    session_id = uuid4()
    repository = FakeAttachmentRepository()
    index_use_case = MagicMock()

    use_case = CreateChatAttachmentUseCase(
        attachment_repository=repository,
        session_repository=FakeSessionRepository(user_id),
        storage_root=str(tmp_path),
        index_attachment_use_case=index_use_case,
    )

    content = b"# Teste\n\n"

    result = use_case.execute(
        CreateChatAttachmentRequest(
            user_id=str(user_id),
            session_id=str(session_id),
            original_filename="nota.md",
            content_type="text/markdown",
            size_bytes=len(content),
            content=content,
        )
    )

    index_use_case.execute.assert_not_called()
    assert result.status == "indexing"
    assert len(repository.status_updates) == 1
    assert repository.status_updates[0]["status"] == "indexing"


def test_create_attachment_indexes_sync_when_async_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_ATTACHMENT_ASYNC_INDEX", "false")
    Settings.CHAT_ATTACHMENT_ASYNC_INDEX = False

    user_id = uuid4()
    session_id = uuid4()
    repository = FakeAttachmentRepository()
    index_use_case = MagicMock()

    use_case = CreateChatAttachmentUseCase(
        attachment_repository=repository,
        session_repository=FakeSessionRepository(user_id),
        storage_root=str(tmp_path),
        index_attachment_use_case=index_use_case,
    )

    content = b"# Teste\n\n"

    use_case.execute(
        CreateChatAttachmentRequest(
            user_id=str(user_id),
            session_id=str(session_id),
            original_filename="nota.md",
            content_type="text/markdown",
            size_bytes=len(content),
            content=content,
        )
    )

    index_use_case.execute.assert_called_once()
