from app.domain.services.chat_drawing_native_text_gate_service import (
    ChatDrawingNativeTextGateService,
)


def test_native_gate_forces_ocr_when_filename_present_without_labeled_code():
    plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
        "POS CODIGO QTD\n10020031 1\nREV. 00\nCLIENTE WEG",
        product_code=None,
        filename_code="90261893",
    )

    assert plausible is False
    plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
        "some random text without stamp",
        product_code="926485",
        filename_code="90264085",
    )

    assert plausible is False


def test_accepts_matching_primary_code_and_filename():
    plausible = ChatDrawingNativeTextGateService.is_native_text_plausible(
        "CODIGO DELPI 90264226 REV 00",
        product_code="90264226",
        filename_code="90264226",
    )

    assert plausible is True
