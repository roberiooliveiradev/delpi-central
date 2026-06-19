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


def test_extract_dimensions_cota_deape_length_pattern():
    text = "MEDIDAS EM MILÍMETROS\n6±140±1\n6±150±1\nDECAPE DE 6MM"

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] == 6.0
    assert dims["rightDecapeMm"] == 6.0
    assert dims["totalLengthMm"] == 150.0
    assert dims["cotaDecapeValuesMm"] == [6.0]
    assert 140.0 in dims["segmentLengthsMm"]
    assert 150.0 in dims["segmentLengthsMm"]


def test_extract_dimensions_machine_side_note_sets_left_decape():
    text = "DECAPE DE 6MM\nDECAPAR O LADO DE 4MM NA MÁQUINA"

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] == 4.0
    assert dims["rightDecapeMm"] == 6.0
