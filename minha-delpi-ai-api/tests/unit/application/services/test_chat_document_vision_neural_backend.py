from unittest.mock import patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.infrastructure.config.settings import Settings


def test_docling_backend_falls_back_to_native(monkeypatch):
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_ENABLED", "true")
    monkeypatch.setenv("CHAT_DOCUMENT_VISION_BACKEND", "docling")
    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_BACKEND = "docling"

    with patch.object(
        ChatDocumentVisionService,
        "_stage_neural_backend",
        return_value={"fullText": "", "warnings": ["docling_not_installed"]},
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_native",
            return_value={
                "fullText": "TEXTO NATIVO " * 30,
                "engine": "pypdf",
                "legible": True,
                "metadata": {},
            },
        ):
            with patch.object(
                ChatDocumentVisionService,
                "_stage_tesseract_pdf",
                return_value={"fullText": "", "warnings": []},
            ):
                result = ChatDocumentVisionService.extract_from_storage_path(
                    "/tmp/doc.pdf",
                    filename="doc.pdf",
                    content_type="application/pdf",
                )

    assert "native" in (result.get("stages") or [])
    assert any(
        "docling_unavailable_fallback_auto" in str(w) for w in (result.get("warnings") or [])
    )
