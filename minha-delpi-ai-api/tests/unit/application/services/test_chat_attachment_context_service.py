from uuid import uuid4

from app.application.services.chat_attachment_context_service import ChatAttachmentContextService
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
        "agent_key": None,
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


def test_build_context_uses_indexed_chunks():
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
