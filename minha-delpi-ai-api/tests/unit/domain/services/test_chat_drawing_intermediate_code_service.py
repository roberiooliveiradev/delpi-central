from app.domain.services.chat_drawing_intermediate_code_service import (
    ChatDrawingIntermediateCodeService,
)


def test_is_ocr_typo_duplicate_detects_nine_two_swap():
    assert ChatDrawingIntermediateCodeService.is_ocr_typo_duplicate(
        "50295216",
        "50225216",
    )


def test_is_ocr_typo_duplicate_detects_zero_two_swap():
    assert ChatDrawingIntermediateCodeService.is_ocr_typo_duplicate(
        "50204901",
        "50224901",
    )


def test_is_ocr_typo_duplicate_ignores_valid_sibling_intermediates():
    assert not ChatDrawingIntermediateCodeService.is_ocr_typo_duplicate(
        "50225215",
        "50225216",
    )


def test_filter_ocr_duplicates_drops_garbled_row_code():
    bom_sources = [
        (
            "bom_region",
            "50225215\n50225216\n50225217\n50295216",
        )
    ]
    bom_rows = [
        {"code": "50225215"},
        {"code": "50225216"},
        {"code": "50225217"},
        {"code": "50295216"},
    ]

    filtered = ChatDrawingIntermediateCodeService.filter_ocr_duplicates(
        ["50225215", "50225216", "50225217", "50295216"],
        bom_sources=bom_sources,
        bom_rows=bom_rows,
    )

    assert filtered == ["50225215", "50225216", "50225217"]
