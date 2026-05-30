from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.application.use_cases.download_chat_file_use_cases import (
    DownloadChatAttachmentUseCase,
    DownloadChatSourceUseCase,
)
from app.domain.entities.chat_attachment import ChatAttachment
from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)


class FakeAttachmentRepository:
    def __init__(self, attachment: ChatAttachment | None):
        self.attachment = attachment

    def get_attachment_by_id(self, *, user_id: UUID, attachment_id: UUID):
        if self.attachment and self.attachment.id == attachment_id:
            return self.attachment
        return None


class FakeKnowledgeRepository:
    def __init__(self, document: KnowledgeDocument | None):
        self.document = document

    def get_document_by_id(self, document_id: UUID):
        if self.document and self.document.id == document_id:
            return self.document
        return None


class FakeAccessChecker:
    def __init__(self, allowed: bool = True):
        self.allowed = allowed

    def _can_delete(self, *, user_id: str, metadata: dict) -> bool:
        return self.allowed


def _build_attachment(path: Path, user_id: UUID) -> ChatAttachment:
    now = datetime.now(UTC)
    return ChatAttachment(
        id=uuid4(),
        user_id=user_id,
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename=path.name,
        original_filename=path.name,
        content_type="text/plain",
        size_bytes=path.stat().st_size,
        storage_path=str(path),
        status="uploaded",
        metadata={},
        created_at=now,
        updated_at=now,
    )


def test_download_chat_attachment_reads_file(tmp_path) -> None:
    user_id = uuid4()
    file_path = tmp_path / "nota.txt"
    file_path.write_text("conteudo do anexo", encoding="utf-8")

    attachment = _build_attachment(file_path, user_id)
    use_case = DownloadChatAttachmentUseCase(FakeAttachmentRepository(attachment))

    result = use_case.execute(user_id=str(user_id), attachment_id=str(attachment.id))

    assert result.filename == "nota.txt"
    assert result.content == b"conteudo do anexo"
    assert result.content_type == "text/plain"


def test_download_chat_attachment_not_found() -> None:
    use_case = DownloadChatAttachmentUseCase(FakeAttachmentRepository(None))

    with pytest.raises(ChatSessionNotFoundError):
        use_case.execute(user_id=str(uuid4()), attachment_id=str(uuid4()))


def test_download_chat_source_from_storage(tmp_path) -> None:
    user_id = str(uuid4())
    source_id = uuid4()
    file_path = tmp_path / "data_sql_api_instructions.md"
    file_path.write_text("# SQL", encoding="utf-8")

    document = KnowledgeDocument(
        id=source_id,
        title="SQL API",
        source_type="file",
        content="",
        source_ref=str(file_path),
        metadata={
            "scope": "agent_source",
            "agentId": "11111111-1111-4111-8111-111111111111",
            "originalFilename": "data_sql_api_instructions.md",
            "storagePath": str(file_path),
        },
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    use_case = DownloadChatSourceUseCase(
        FakeKnowledgeRepository(document),
        FakeAccessChecker(allowed=True),
    )

    result = use_case.execute(user_id=user_id, source_id=str(source_id))

    assert result.filename == "sql-data-api-instructions.md"
    assert result.content == b"# SQL"


def test_download_chat_source_from_inline_content() -> None:
    user_id = str(uuid4())
    source_id = uuid4()

    document = KnowledgeDocument(
        id=source_id,
        title="Nota do agente",
        source_type="manual",
        content="Texto da nota",
        source_ref=None,
        metadata={"scope": "agent_source", "agentId": "11111111-1111-4111-8111-111111111111"},
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    use_case = DownloadChatSourceUseCase(
        FakeKnowledgeRepository(document),
        FakeAccessChecker(allowed=True),
    )

    result = use_case.execute(user_id=user_id, source_id=str(source_id))

    assert result.filename == "nota-do-agente.md"
    assert result.content == b"Texto da nota"


def test_download_chat_source_access_denied() -> None:
    document = KnowledgeDocument(
        id=uuid4(),
        title="Privado",
        source_type="manual",
        content="x",
        source_ref=None,
        metadata={"scope": "agent_source"},
        active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    use_case = DownloadChatSourceUseCase(
        FakeKnowledgeRepository(document),
        FakeAccessChecker(allowed=False),
    )

    with pytest.raises(ChatSessionAccessDeniedError):
        use_case.execute(user_id=str(uuid4()), source_id=str(document.id))
