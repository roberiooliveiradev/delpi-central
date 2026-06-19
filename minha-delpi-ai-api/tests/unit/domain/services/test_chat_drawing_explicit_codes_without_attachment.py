from app.domain.services.chat_drawing_product_code_resolution_service import (
    ChatDrawingProductCodeResolutionService,
)


def test_resolve_explicit_codes_from_message():
    codes, source = ChatDrawingProductCodeResolutionService.resolve_explicit_codes_without_attachment(
        message="analise os desenhos 90262957 e 90263489",
    )

    assert codes == ("90262957", "90263489")
    assert source == "message"


def test_resolve_explicit_codes_from_context_items():
    codes, source = ChatDrawingProductCodeResolutionService.resolve_explicit_codes_without_attachment(
        message="analise o desenho",
        user_context_items=[
            {"kind": "context", "content": "90262957"},
            {"kind": "context", "content": "90263489"},
        ],
    )

    assert codes == ("90262957", "90263489")
    assert source == "context"


def test_resolve_explicit_codes_empty_without_message_or_context():
    codes, source = ChatDrawingProductCodeResolutionService.resolve_explicit_codes_without_attachment(
        message="analise o desenho",
        user_context_items=[],
    )

    assert codes == ()
    assert source is None
