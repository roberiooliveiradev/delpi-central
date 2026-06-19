from pathlib import Path

from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_pdf_document_extraction_service import (
    ChatPdfDocumentExtractionService,
)
from app.domain.services.chat_pdf_embedded_text_service import ChatPdfEmbeddedTextService


def test_embedded_text_reads_oda_annotations_from_90262019():
    pdf = Path(__file__).resolve().parents[3] / "desenhos" / "90262019.pdf"

    if not pdf.is_file():
        return

    embedded = ChatPdfEmbeddedTextService.extract(str(pdf))

    assert embedded["supported"] is True
    assert embedded["annotationCount"] >= 50
    assert len(embedded.get("annotations") or []) >= 50
    assert "90262019" in embedded["annotationText"]
    assert "10080591" in embedded["annotationText"]
    assert "10090481" in embedded["annotationText"]
    assert "10250032" in embedded["annotationText"]
    assert embedded["pdfMetadata"].get("producer", "").lower().find("oda") >= 0


def test_document_extraction_fuses_90262019_without_region_ocr():
    pdf = Path(__file__).resolve().parents[3] / "desenhos" / "90262019.pdf"

    if not pdf.is_file():
        return

    extracted = ChatPdfDocumentExtractionService.extract_from_storage_path(
        str(pdf),
        filename="90262019.pdf",
        layout_profile=ChatPdfDocumentExtractionService.LAYOUT_GENERIC,
        enable_region_ocr=False,
    )

    assert extracted["supported"] is True
    assert extracted["charCount"] > 200
    assert "fitz_embedded" in extracted["stages"]
    assert "region_ocr" not in extracted["stages"]
    assert "90262019" in extracted["fullText"]
    assert "10090481" in extracted["fullText"]


def test_drawing_extraction_builds_bom_for_90262019():
    pdf = Path(__file__).resolve().parents[3] / "desenhos" / "90262019.pdf"

    if not pdf.is_file():
        return

    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf),
        filename="90262019.pdf",
    )

    assert parsed["productCode"] == "90262019"
    assert parsed["componentCodes"] == ["10250032", "10080591", "10090481"]
    assert len(parsed.get("bomRows") or []) >= 3
