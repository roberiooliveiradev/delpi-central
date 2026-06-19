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


def test_parse_with_bom_region_keeps_stamp_product_code():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "10400006 aparece antes no texto global",
        metadata={
            "stampText": "CODIGO DELPI 90261040",
            "bomText": "01 10400006 2 TERMINAL",
        },
    )

    assert parsed["productCode"] == "90261040"
    assert any(row["code"] == "10400006" for row in parsed.get("bomRows") or [])


def test_parse_with_stamp_text_skips_global_fallback_code():
    parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "90288888 no corpo sem carimbo legivel",
        metadata={"stampText": "CARIMBO ILEGIVEL"},
    )

    assert parsed.get("productCode") is None
