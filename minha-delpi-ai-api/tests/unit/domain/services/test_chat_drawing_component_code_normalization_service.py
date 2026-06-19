from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)


def test_normalize_extracted_preserves_digits_read_from_pdf():
    assert (
        ChatDrawingComponentCodeNormalizationService.normalize_extracted("40091640")
        == "40091640"
    )
    assert (
        ChatDrawingComponentCodeNormalizationService.normalize_extracted("1013091")
        == "1013091"
    )
