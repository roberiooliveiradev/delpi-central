from pathlib import Path

from app.domain.services.chat_pdf_document_extraction_service import (
    ChatPdfDocumentExtractionService,
)


def test_attachment_index_triggers_tesseract_when_embedded_insufficient(
    monkeypatch,
    tmp_path,
):
    path = Path(tmp_path) / "scan.pdf"
    path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        ChatPdfDocumentExtractionService,
        "extract_from_storage_path",
        classmethod(
            lambda cls, *args, **kwargs: {
                "supported": True,
                "fullText": "curto",
                "stages": ["pypdf"],
                "parseMetadata": {},
                "annotationTables": [],
                "engine": "pypdf",
                "warnings": [],
            }
        ),
    )
    monkeypatch.setattr(
        "app.domain.services.chat_pdf_page_tesseract_ocr_service.ChatPdfPageTesseractOcrService.extract_text",
        lambda *args, **kwargs: {
            "fullText": "Texto OCR da página escaneada com conteúdo suficiente para indexação.",
            "warnings": [],
        },
    )

    result = ChatPdfDocumentExtractionService.extract_for_attachment_index(
        str(path),
        filename="scan.pdf",
    )

    assert result["supported"] is True
    assert "attachment_index_tesseract" in result["metadata"]["stages"]
    assert "Texto OCR da página escaneada" in result["content"]
    assert result["metadata"]["attachmentIndexOcr"]["engine"] == "tesseract_page"
