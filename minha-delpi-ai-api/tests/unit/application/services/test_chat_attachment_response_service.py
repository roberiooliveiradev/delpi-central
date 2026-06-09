from app.application.services.chat_attachment_response_service import (
    ChatAttachmentResponseService,
)
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4


def test_to_response_includes_reading_status_and_preview():
    attachment = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename="file.csv",
        original_filename="dados.csv",
        content_type="text/csv",
        size_bytes=120,
        status="indexed",
        metadata={
            "indexed": True,
            "preview": {
                "kind": "spreadsheet",
                "columns": ["Produto", "Qtd"],
            },
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = ChatAttachmentResponseService.to_response(attachment)

    assert response.metadata is not None
    assert response.metadata["readingStatus"] == "Indexado"
    assert response.metadata["preview"]["columns"] == ["Produto", "Qtd"]


def test_to_response_includes_document_vision_summary():
    attachment = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename="doc.pdf",
        original_filename="doc.pdf",
        content_type="application/pdf",
        size_bytes=1200,
        status="indexed",
        metadata={
            "indexed": True,
            "documentVision": {
                "engine": "tesseract",
                "legible": True,
                "legibilityScore": 0.8,
                "bomRowCount": 2,
                "hasTitleBlock": True,
                "tableCount": 1,
                "stages": ["native", "tesseract_pdf"],
            },
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = ChatAttachmentResponseService.to_response(attachment)

    summary = response.metadata.get("documentVisionSummary")

    assert summary["engine"] == "tesseract"
    assert summary["bomRowCount"] == 2
    assert "visão (tesseract)" in response.metadata["readingStatus"]


def test_to_response_legacy_doc_reading_status():
    attachment = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename="ata.doc",
        original_filename="ata.doc",
        content_type="application/msword",
        size_bytes=4096,
        status="unsupported",
        metadata={
            "indexed": False,
            "indexReason": {
                "reason": "legacy_doc_format",
                "userHint": "Salve como DOCX.",
            },
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = ChatAttachmentResponseService.to_response(attachment)

    assert response.metadata is not None
    assert response.metadata["readingStatus"] == "DOC legado — salve como DOCX"


def test_to_response_index_failed_with_legible_document_vision():
    attachment = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename="desenho.pdf",
        original_filename="desenho.pdf",
        content_type="application/pdf",
        size_bytes=1200,
        status="index_failed",
        metadata={
            "indexed": False,
            "documentVision": {
                "engine": "tesseract",
                "legible": True,
                "legibilityScore": 0.82,
                "bomRowCount": 3,
                "hasTitleBlock": True,
                "tableCount": 0,
                "stages": ["native", "tesseract_pdf"],
            },
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = ChatAttachmentResponseService.to_response(attachment)

    assert response.metadata is not None
    assert response.metadata["readingStatus"] == "Legível por visão (tesseract)"
