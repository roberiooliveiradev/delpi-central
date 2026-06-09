from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)


def test_parse_prefers_chicote_title_over_first_bom_code():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "CHICOTE DE LIGAÇÃO90264236\n"
        "10090061 TERM PINO\n"
        "10080141 CABO",
    )

    assert parsed["productCode"] == "90264236"
    assert parsed.get("productCodeSource") == "title_pattern"


def test_parse_labeled_stamp_code():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "CÓDIGO DELPI 90264234\nCOD: 19402706",
    )

    assert parsed["productCode"] == "90264234"
    assert parsed.get("productCodeSource") == "stamp_labeled"
