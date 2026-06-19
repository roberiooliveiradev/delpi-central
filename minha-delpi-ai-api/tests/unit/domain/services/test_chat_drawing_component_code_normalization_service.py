from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)


def test_normalize_extracted_ocr_typos():
    assert (
        ChatDrawingComponentCodeNormalizationService.normalize_extracted("40091640")
        == "10091640"
    )
    assert (
        ChatDrawingComponentCodeNormalizationService.normalize_extracted("1013091")
        == "10130091"
    )


def test_reconcile_with_known_requires_catalog_match_for_ambiguous():
    known = {"10091640", "10130091"}

    assert (
        ChatDrawingComponentCodeNormalizationService.reconcile_with_known(
            "40091640",
            known,
        )
        == "10091640"
    )
