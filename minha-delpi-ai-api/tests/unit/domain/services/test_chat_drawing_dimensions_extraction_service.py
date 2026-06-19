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


def test_merge_dimensions_prefers_fallback_decape_when_region_is_bom_table():
    region = "50215425 CT26VERM-00036/04/06-0000 10440133"
    fallback = "DECAPE DE 6MM\nDECAPAR O LADO DE 4MM NA MÁQUINA\n6±140±1"

    merged = ChatDrawingDimensionsExtractionService.merge_dimensions(
        {},
        region_text=region,
        fallback_text=fallback,
    )

    assert merged["leftDecapeMm"] == 4.0
    assert merged["rightDecapeMm"] == 6.0
    assert 140.0 in merged["segmentLengthsMm"]


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


def test_extract_dimensions_segment_and_decape_tolerance_cad():
    text = "\n".join(["10±1", "1127±2"] * 4)

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] is None
    assert dims["rightDecapeMm"] == 10.0
    assert dims["decapeIndication"] == {"left": False, "right": True}
    assert dims["totalLengthMm"] == 1127.0
    assert dims["segmentLengthsMm"] == [1127.0, 1127.0, 1127.0, 1127.0]


def test_extract_dimensions_rejects_glued_tolerance_cota():
    text = "ABC 10±11127±2\nEBC 10±11127±2"

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["totalLengthMm"] == 1127.0
    assert dims["rightDecapeMm"] == 10.0
    assert dims["leftDecapeMm"] is None
    assert 11127.0 not in (dims.get("segmentLengthsMm") or [])


def test_merge_dimensions_prefers_cad_fallback_when_fused_length_implausible():
    fused = "ABC 10±11127±2\nEBC 10±11127±2"
    cad = "\n".join(["10±1", "1127±2"] * 2)

    merged = ChatDrawingDimensionsExtractionService.merge_dimensions(
        ChatDrawingDimensionsExtractionService.extract_dimensions(fused),
        fallback_text=cad,
    )

    assert merged["totalLengthMm"] == 1127.0
    assert merged["rightDecapeMm"] == 10.0
    assert merged["leftDecapeMm"] is None


def test_extract_dimensions_length_first_cota_assigns_left_decape():
    text = """
    MEDIDAS EM MILÍMETRO
    240 ±2 11 ±1
    238 ±2 11 ±1
    """

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] == 11.0
    assert dims["rightDecapeMm"] is None
    assert dims["decapeIndication"] == {"left": True, "right": False}
    assert dims["totalLengthMm"] == 240.0
    assert 238.0 in dims["segmentLengthsMm"]


def test_extract_dimensions_ignores_shrink_wrap_only_context():
    text = "LUVA TERMO ENCOLHIVEL 9,50X0,60 COMP 30MM"

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] is None
    assert dims["rightDecapeMm"] is None


def test_detect_ambiguous_dimension_notes_when_shrink_and_decape_coexist():
    text = "LUVA TERMO ENCOLHIVEL COMP 30MM\nDECAPE DE 6MM"

    assert ChatDrawingDimensionsExtractionService.detect_ambiguous_dimension_notes(text)


def test_extract_dimensions_ignores_process_sample_30mm():
    text = "PONTA DE ENSAIO COMP 30MM\n30±1"

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] is None
    assert dims["rightDecapeMm"] is None
    assert dims["decapeIndication"] == {"left": False, "right": False}


def test_extract_dimensions_rejects_unlabeled_30mm_tolerance():
    text = "\n".join(["30±1", "1127±2"] * 2)

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] is None
    assert dims["rightDecapeMm"] is None


def test_only_implausible_global_decape_when_all_values_above_typical():
    assert ChatDrawingDimensionsExtractionService.only_implausible_global_decape(
        {"leftDecapeMm": 30.0, "rightDecapeMm": 30.0}
    )
    assert not ChatDrawingDimensionsExtractionService.only_implausible_global_decape(
        {"leftDecapeMm": 10.0, "rightDecapeMm": None}
    )