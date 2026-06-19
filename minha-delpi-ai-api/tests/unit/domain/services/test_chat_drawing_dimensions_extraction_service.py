from app.domain.services.chat_drawing_dimensions_extraction_service import (
    ChatDrawingDimensionsExtractionService,
)


def test_extract_dimensions_ocr_tolerant_deape_and_compr():
    text = """
    COMPR TOTAL 1 400 mm
    DEC4PE ESQUERDO 10
    DECAPE DIREITO 12,5
    """

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["totalLengthMm"] == 1400.0
    assert dims["leftDecapeMm"] == 10.0
    assert dims["rightDecapeMm"] == 12.5


def test_merge_dimensions_prefers_region_text():
    merged = ChatDrawingDimensionsExtractionService.merge_dimensions(
        {"totalLengthMm": 100.0, "leftDecapeMm": None, "rightDecapeMm": None},
        region_text="DECAPE ESQUERDO 8\nDECAPE DIREITO 9",
        fallback_text="COMPRIMENTO TOTAL 999 mm",
    )

    assert merged["totalLengthMm"] == 100.0
    assert merged["leftDecapeMm"] == 8.0
    assert merged["rightDecapeMm"] == 9.0
