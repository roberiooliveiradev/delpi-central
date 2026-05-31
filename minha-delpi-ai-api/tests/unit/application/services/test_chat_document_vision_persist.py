from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.services.chat_document_vision_service import ChatDocumentVisionService


def test_persist_attachment_vision_metadata_updates_repository():
    attachment_id = uuid4()
    attachment = MagicMock()
    attachment.id = attachment_id
    attachment.status = "indexed"

    with patch(
        "app.infrastructure.persistence.postgres_chat_attachment_repository.PostgresChatAttachmentRepository"
    ) as repo_cls:
        repo = repo_cls.return_value
        ChatDocumentVisionService.persist_attachment_vision_metadata(
            attachment,
            {"engine": "tesseract", "stages": ["tesseract"]},
        )

    repo.update_status.assert_called_once()
    call_kwargs = repo.update_status.call_args.kwargs
    assert call_kwargs["attachment_id"] == attachment_id
    assert call_kwargs["status"] == "indexed"
    assert call_kwargs["metadata"]["documentVision"]["engine"] == "tesseract"
    assert call_kwargs["metadata"]["documentVisionAt"]


def test_refresh_attachment_vision_snapshot_persists(monkeypatch):
    attachment = MagicMock()
    attachment.id = uuid4()
    attachment.status = "ready"
    attachment.original_filename = "doc.pdf"
    attachment.content_type = "application/pdf"
    attachment.storage_path = "/tmp/doc.pdf"

    with patch.object(
        ChatDocumentVisionService,
        "_compute_vision_for_attachment",
        return_value={
            "engine": "native",
            "stages": ["native"],
            "charCount": 120,
            "legible": True,
            "legibilityScore": 0.9,
            "schemaVersion": "1.0",
        },
    ):
        with patch.object(
            ChatDocumentVisionService,
            "persist_attachment_vision_metadata",
        ) as persist_mock:
            meta = ChatDocumentVisionService.refresh_attachment_vision_snapshot(
                attachment,
                skills={"documentVision": True},
            )

    assert meta["engine"] == "native"
    persist_mock.assert_called_once()
