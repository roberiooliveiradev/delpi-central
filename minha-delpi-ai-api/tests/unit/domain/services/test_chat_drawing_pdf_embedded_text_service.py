from tests.support.drawing_pdf_fixtures import require_drawing_pdf

from app.domain.services.chat_drawing_pdf_embedded_text_service import (
    ChatDrawingPdfEmbeddedTextService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_pdf_embedded_text_service import ChatPdfEmbeddedTextService


def test_embedded_alias_delegates_to_chat_base():
    pdf = require_drawing_pdf("90262019.pdf")

    base = ChatPdfEmbeddedTextService.extract(str(pdf))
    alias = ChatDrawingPdfEmbeddedTextService.extract(str(pdf))

    assert alias["supported"] == base["supported"]
    assert alias["combinedText"] == base["combinedText"]


def test_embedded_text_reads_oda_annotations_from_90262019():
    pdf = require_drawing_pdf("90262019.pdf")

    embedded = ChatDrawingPdfEmbeddedTextService.extract(str(pdf))

    assert embedded["supported"] is True
    assert embedded["annotationCount"] >= 50
    assert "90262019" in embedded["annotationText"]
    assert "10080591" in embedded["annotationText"]
    assert "10090481" in embedded["annotationText"]
    assert "10250032" in embedded["annotationText"]
    assert embedded["pdfMetadata"].get("producer", "").lower().find("oda") >= 0


def test_parse_from_embedded_annotations_builds_bom_for_90262019():
    pdf = require_drawing_pdf("90262019.pdf")

    embedded = ChatDrawingPdfEmbeddedTextService.extract(str(pdf))
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        embedded["combinedText"],
        metadata={
            "extractor": "fitz_embedded",
            "annotationText": embedded["annotationText"],
            "pdfMetadata": embedded["pdfMetadata"],
        },
    )

    assert parsed["productCode"] == "90262019"
    assert set(parsed["componentCodes"]) == {
        "10250032",
        "10080591",
        "10090481",
        "10084053",
    }
    assert len(parsed.get("bomRows") or []) >= 3
