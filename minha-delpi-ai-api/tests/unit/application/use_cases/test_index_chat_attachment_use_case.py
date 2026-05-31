from dataclasses import dataclass
from unittest.mock import patch
from uuid import uuid4

from app.application.use_cases.index_chat_attachment_use_case import (
    IndexChatAttachmentUseCase,
)
from app.infrastructure.config.settings import Settings


@dataclass
class FakeAttachment:
    id: object
    user_id: object
    session_id: object
    message_id: object | None
    project_id: object | None
    agent_id: str | None
    storage_path: str
    original_filename: str
    content_type: str
    status: str = "uploaded"


class FakeAttachmentRepository:
    def __init__(self):
        self.updated = []

    def update_status(self, *, attachment_id, status, metadata):
        self.updated.append(
            {
                "attachment_id": attachment_id,
                "status": status,
                "metadata": metadata,
            }
        )

        return type("UpdatedAttachment", (), {"status": status})()


class FakeIngestUseCase:
    def __init__(self):
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return {
            "id": str(uuid4()),
            "title": request.title,
            "chunks": 1,
        }


class FakeTextExtractor:
    def extract(self, *, storage_path, filename, content_type):
        return {
            "supported": True,
            "content": "# Documento\n\nConteúdo de teste.",
            "metadata": {
                "extractor": "plain_text",
                "extension": ".md",
            },
        }


def test_index_chat_attachment_uses_session_source_scope():
    attachment_id = uuid4()
    user_id = uuid4()
    session_id = uuid4()
    message_id = uuid4()
    project_id = uuid4()

    repository = FakeAttachmentRepository()
    ingest = FakeIngestUseCase()

    use_case = IndexChatAttachmentUseCase(
        attachment_repository=repository,
        ingest_knowledge_document_use_case=ingest,
        text_extractor=FakeTextExtractor(),
    )

    result = use_case.execute(
        user_id=str(user_id),
        attachment=FakeAttachment(
            id=attachment_id,
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            project_id=project_id,
            agent_id="11111111-1111-4111-8111-111111111111",
            storage_path="/tmp/documento.md",
            original_filename="documento.md",
            content_type="text/markdown",
        ),
    )

    assert result["indexed"] is True
    assert len(ingest.requests) == 1

    request = ingest.requests[0]

    assert request.source_type == "chat_attachment"
    assert request.source_ref == str(attachment_id)
    assert request.metadata["scope"] == "session_source"
    assert request.metadata["userId"] == str(user_id)
    assert request.metadata["sessionId"] == str(session_id)
    assert request.metadata["messageId"] == str(message_id)
    assert request.metadata["projectId"] == str(project_id)
    assert request.metadata["agentId"] == "11111111-1111-4111-8111-111111111111"
    assert request.metadata["attachmentId"] == str(attachment_id)
    assert request.metadata["originalFilename"] == "documento.md"


def test_index_pdf_triggers_vision_snapshot_when_enabled(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True

    attachment_id = uuid4()
    repository = FakeAttachmentRepository()
    ingest = FakeIngestUseCase()

    use_case = IndexChatAttachmentUseCase(
        attachment_repository=repository,
        ingest_knowledge_document_use_case=ingest,
        text_extractor=FakeTextExtractor(),
    )

    with patch(
        "app.application.services.chat_document_vision_service.ChatDocumentVisionService.refresh_attachment_vision_snapshot"
    ) as refresh_mock:
        use_case.execute(
            user_id=str(uuid4()),
            attachment=FakeAttachment(
                id=attachment_id,
                user_id=uuid4(),
                session_id=uuid4(),
                message_id=None,
                project_id=None,
                agent_id=None,
                storage_path="/tmp/desenho.pdf",
                original_filename="desenho.pdf",
                content_type="application/pdf",
            ),
        )

    refresh_mock.assert_called_once()
