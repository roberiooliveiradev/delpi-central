from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)


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
