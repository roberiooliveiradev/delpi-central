from unittest.mock import patch
from uuid import uuid4

from app.application.services.chat_attachment_context_service import ChatAttachmentContextService
from app.infrastructure.config.settings import Settings
from app.domain.entities.chat_attachment import ChatAttachment
from app.domain.entities.knowledge_chunk import KnowledgeChunk
from datetime import datetime, timezone


class FakeAttachmentRepository:
    def __init__(self, attachments):
        self.attachments = attachments

    def list_attachments_by_ids(self, *, user_id, session_id, attachment_ids):
        return self.attachments


class FakeKnowledgeRepository:
    def __init__(self, chunks):
        self.chunks = chunks

    def list_chunks_by_document_id(self, document_id, *, limit=12):
        return self.chunks


class FakeTextExtractor:
    def extract(self, **kwargs):
        return {
            "supported": True,
            "content": "conteúdo extraído on demand",
            "metadata": {},
        }


def _attachment(**overrides):
    now = datetime.now(timezone.utc)
    base = {
        "id": uuid4(),
        "user_id": uuid4(),
        "session_id": uuid4(),
        "message_id": None,
        "project_id": None,
        "agent_id": None,
        "filename": "doc.md",
        "original_filename": "doc.md",
        "content_type": "text/markdown",
        "size_bytes": 10,
        "storage_path": "/tmp/doc.md",
        "status": "indexed",
        "metadata": {"knowledgeDocumentId": str(uuid4())},
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    return ChatAttachment(**base)


def test_build_context_uses_indexed_chunks(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "false")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = False

    document_id = uuid4()
    attachment = _attachment(
        metadata={"knowledgeDocumentId": str(document_id)},
    )

    service = ChatAttachmentContextService(
        attachment_repository=FakeAttachmentRepository([attachment]),
        knowledge_repository=FakeKnowledgeRepository(
            [
                KnowledgeChunk(
                    id=uuid4(),
                    document_id=document_id,
                    chunk_index=0,
                    content="Trecho indexado do manual",
                    metadata={},
                    created_at=datetime.now(timezone.utc),
                    score=None,
                    title="doc.md",
                    source_type="chat_attachment",
                    source_ref=str(attachment.id),
                )
            ]
        ),
        text_extractor=FakeTextExtractor(),
    )

    result = service.build_context(
        user_id=attachment.user_id,
        session_id=attachment.session_id,
        attachment_ids=[attachment.id],
    )

    assert "Trecho indexado do manual" in result
    assert "### doc.md" in result


def test_build_context_ocr_image_replaces_placeholder(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True

    attachment = _attachment(
        filename="scan.png",
        original_filename="scan.png",
        content_type="image/png",
        storage_path="/tmp/scan.png",
        status="ready",
        metadata={},
    )

    service = ChatAttachmentContextService(
        attachment_repository=FakeAttachmentRepository([attachment]),
        knowledge_repository=FakeKnowledgeRepository([]),
        text_extractor=FakeTextExtractor(),
    )

    class ImagePlaceholderExtractor:
        def extract(self, **kwargs):
            return {
                "supported": True,
                "content": (
                    "[Imagem scan.png. Conteúdo visual indexado por metadados; "
                    "descreva o que precisa.]"
                ),
                "metadata": {"extractor": "image_metadata"},
            }

    service.text_extractor = ImagePlaceholderExtractor()

    with patch(
        "app.application.services.chat_attachment_context_service.ChatDocumentVisionService.extract_from_storage_path",
        return_value={"fullText": "CODIGO 90260199 REV.04", "legible": True},
    ):
        result = service.build_context(
            user_id=attachment.user_id,
            session_id=attachment.session_id,
            attachment_ids=[attachment.id],
        )

    assert "90260199" in result
    assert "Conteúdo visual indexado" not in result


def test_build_context_indexed_short_chunks_falls_back_to_ocr(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_MIN_LEGIBLE_CHARS = 40

    document_id = uuid4()
    attachment = _attachment(
        filename="scan.pdf",
        original_filename="scan.pdf",
        content_type="application/pdf",
        storage_path="/tmp/scan.pdf",
        status="indexed",
        metadata={"knowledgeDocumentId": str(document_id)},
    )

    service = ChatAttachmentContextService(
        attachment_repository=FakeAttachmentRepository([attachment]),
        knowledge_repository=FakeKnowledgeRepository(
            [
                KnowledgeChunk(
                    id=uuid4(),
                    document_id=document_id,
                    chunk_index=0,
                    content="curto",
                    metadata={},
                    created_at=datetime.now(timezone.utc),
                    score=None,
                    title="scan.pdf",
                    source_type="chat_attachment",
                    source_ref=str(attachment.id),
                )
            ]
        ),
        text_extractor=FakeTextExtractor(),
    )

    with patch(
        "app.application.services.chat_attachment_context_service.ChatDocumentVisionService.enrich_attachment_excerpt",
        return_value="TEXTO LONGO DE OCR " * 20,
    ) as enrich_mock:
        result = service.build_context(
            user_id=attachment.user_id,
            session_id=attachment.session_id,
            attachment_ids=[attachment.id],
        )

    enrich_mock.assert_called_once()
    assert "TEXTO LONGO DE OCR" in result
