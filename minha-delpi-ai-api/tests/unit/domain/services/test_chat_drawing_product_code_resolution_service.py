from app.domain.services.chat_drawing_native_text_gate_service import (
    ChatDrawingNativeTextGateService,
)
from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)


def test_native_gate_rejects_bom_code_with_primary_filename():
    plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
        "POS CODIGO QTD\n10020031 1\n10020032 2",
        product_code="10020031",
        filename_code="90261893",
    )

    assert plausible is False


def test_native_gate_accepts_stamp_markers():
    plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
        "CÓDIGO DELPI 90262379\nREV. 01\nCLIENTE WEG",
        product_code="90262379",
        filename_code="90262379",
    )

    assert plausible is True


def test_resolve_prefers_filename_over_conflicting_pdf_extract():
    code, source = ChatDrawingProductCodeResolutionService.resolve(
        message="analise o desenho tecnico",
        has_pdf_attachment=True,
        pdf_extract={"productCode": "10070077", "legible": True},
        attachment_filename="90262511.pdf",
    )

    assert code == "90262511"
    assert source == "filename"


def test_resolve_uses_message_code_over_filename():
    code, source = ChatDrawingProductCodeResolutionService.resolve(
        message="analise o desenho 90260140",
        has_pdf_attachment=True,
        pdf_extract={"productCode": "90262511"},
        attachment_filename="90262511.pdf",
    )

    assert code == "90260140"
    assert source == "message"


def test_resolve_uses_stamp_candidates_when_pdf_code_missing():
    code, source = ChatDrawingProductCodeResolutionService.resolve(
        message="analise o desenho",
        has_pdf_attachment=True,
        pdf_extract={
            "productCode": None,
            "productCodeCandidates": [
                {"code": "90264234", "source": "stamp_labeled", "confidence": 0.92},
            ],
        },
        attachment_filename="90264234.pdf",
    )

    assert code == "90264234"
    assert source in {"stamp_labeled", "filename"}


def test_resolve_rejects_bom_pdf_code_when_filename_is_primary():
    code, source = ChatDrawingProductCodeResolutionService.resolve(
        message="analise o desenho",
        has_pdf_attachment=True,
        pdf_extract={
            "productCode": "10020031",
            "productCodeSource": "pdf_extract",
        },
        attachment_filename="90261893.pdf",
    )

    assert code == "90261893"
    assert source == "filename"


def test_pick_from_candidates_prefers_high_confidence_stamp():
    code, source = ChatDrawingProductCodeResolutionService.pick_from_candidates(
        [
            {"code": "90264234", "source": "stamp_labeled", "confidence": 0.92},
            {"code": "90264235", "source": "stamp_context", "confidence": 0.55},
        ],
    )

    assert code == "90264234"
    assert source == "stamp_labeled"


def test_pick_from_candidates_unresolved_on_conflicting_high_confidence():
    code, source = ChatDrawingProductCodeResolutionService.pick_from_candidates(
        [
            {"code": "90264234", "source": "stamp_labeled", "confidence": 0.92},
            {"code": "90264235", "source": "title_pattern", "confidence": 0.88},
        ],
    )

    assert code is None
    assert source == "unresolved"


def test_enrich_pdf_extract_flags_bom_promotion():
    enriched = ChatDrawingProductCodeResolutionService.enrich_pdf_extract_conflicts(
        {"productCode": "10020031"},
        attachment_filename="90261893.pdf",
    )

    assert enriched["productCode"] == "90261893"
    assert enriched["productCodeSource"] == "filename_crosscheck"
    assert any(item["type"] == "bom_code_promoted" for item in enriched["conflicts"])


def test_merge_precedence_filename_beats_turn_context():
    merged_code, merged_source = ChatDrawingProductCodeResolutionService.merge_precedence(
        current_code="10070077",
        current_source="turn",
        resolved_code="90262511",
        resolved_source="filename",
    )

    assert merged_code == "90262511"
    assert merged_source == "filename"


def test_extract_product_code_from_filename():
    assert (
        ChatDrawingProductCodeResolutionService.extract_product_code_from_filename(
            "90262511.pdf"
        )
        == "90262511"
    )
