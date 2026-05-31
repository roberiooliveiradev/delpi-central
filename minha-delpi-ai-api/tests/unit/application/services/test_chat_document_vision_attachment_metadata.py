from unittest.mock import MagicMock, patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.infrastructure.config.settings import Settings


def test_build_attachment_vision_metadata_indexed_native_lightweight(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True

    attachment = MagicMock()
    attachment.status = "indexed"
    attachment.storage_path = "/tmp/boleto.pdf"
    attachment.original_filename = "BOLETO CNU.pdf"
    attachment.content_type = "application/pdf"

    with patch.object(
        ChatDocumentVisionService,
        "_resolve_first_document_attachment",
        return_value=attachment,
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_native",
            return_value={
                "fullText": "Nome do Pagador ROBERIO TEIXEIRA DE OLIVEIRA " * 3,
                "engine": "pypdf",
                "metadata": {},
            },
        ):
            meta = ChatDocumentVisionService.build_attachment_vision_metadata(
                user_id="user",
                session_id="session",
                attachment_ids=["att-1"],
                skills={"documentVision": True},
            )

    assert meta is not None
    assert meta["engine"] == "pypdf"
    assert meta["stages"] == ["native"]
    assert int(meta.get("charCount") or 0) > 0


def test_build_attachment_vision_metadata_scanned_indexed_runs_full_pipeline(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True

    attachment = MagicMock()
    attachment.status = "indexed"
    attachment.storage_path = "/tmp/scan.pdf"
    attachment.original_filename = "scan.pdf"
    attachment.content_type = "application/pdf"

    with patch.object(
        ChatDocumentVisionService,
        "_resolve_first_document_attachment",
        return_value=attachment,
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_native",
            return_value={"fullText": "", "engine": "pypdf", "metadata": {}},
        ):
            with patch.object(
                ChatDocumentVisionService,
                "extract_from_storage_path",
                return_value={
                    "schemaVersion": "1.0",
                    "engine": "tesseract",
                    "stages": ["native", "tesseract"],
                    "charCount": 200,
                    "legible": True,
                    "durationMs": 50,
                },
            ) as full_extract:
                meta = ChatDocumentVisionService.build_attachment_vision_metadata(
                    user_id="user",
                    session_id="session",
                    attachment_ids=["att-1"],
                    skills={"documentVision": True},
                )

    full_extract.assert_called_once()
    assert meta["engine"] == "tesseract"
