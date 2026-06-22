"""Confiança composta da leitura PDF — gate ≥ 95%."""

from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)


def _low_confidence_pdf_extract() -> dict:
    return {
        "productCode": "90264227",
        "revision": "21",
        "legible": True,
        "componentCodes": ["10440134", "50215426"],
        "documentVision": {
            "legibilityScore": 1.0,
            "hasTitleBlock": False,
            "stages": ["fitz_embedded", "region_ocr"],
        },
        "validationScopes": {"bom": {"available": True}},
    }


def test_resolve_gate_confidence_prefers_retry_metadata():
    result = ChatDrawingExtractionConfidenceService.resolve_gate_confidence(
        pdf_extract={
            "productCode": "90262019",
            "extractionQualityRetry": {
                "selectedConfidence": {
                    "score": 0.96,
                    "threshold": 0.95,
                    "meetsThreshold": True,
                    "components": {"legibility": 0.96},
                    "reasons": [],
                }
            },
        }
    )

    assert result.meets_threshold is True
    assert result.score_percent == 96


def test_extraction_confidence_below_threshold_without_title_block():
    result = ChatDrawingExtractionConfidenceService.evaluate(
        pdf_extract=_low_confidence_pdf_extract(),
        items=[
            {
                "templateKey": "bom_extra_item",
                "status": "critical_error",
            },
            {
                "templateKey": "segment_length_pending",
                "status": "pending",
            },
        ],
    )

    assert result.threshold_percent == 95
    assert result.score_percent < 95
    assert result.meets_threshold is False
    assert "stamp_block_missing" in result.reasons


def test_evaluate_for_extraction_reaches_target_with_rich_bom_read():
    result = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
        pdf_extract={
            "productCode": "90264227",
            "revision": "02",
            "legible": True,
            "charCount": 1200,
            "componentCodes": ["10081867", "50215425", "10440134", "50215433"],
            "intermediateCodes": ["50215425", "50215433"],
            "validationScopes": {"bom": {"available": True}},
            "dimensions": {
                "leftDecapeMm": 4.0,
                "segmentLengthsMm": [140.0, 150.0],
            },
            "sourceMetadata": {"stages": ["region_ocr"]},
        }
    )

    assert result.meets_threshold is True
    assert result.score_percent >= 95


def test_evaluate_for_extraction_flat_mp_bom_without_intermediates():
    result = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
        pdf_extract={
            "productCode": "90264243",
            "legible": True,
            "charCount": 900,
            "componentCodes": ["10080308", "10080843", "10130006", "10420396"],
            "intermediateCodes": [],
            "validationScopes": {"bom": {"available": True}},
            "dimensions": {"leftDecapeMm": 8.0, "rightDecapeMm": 15.0},
            "sourceMetadata": {"stages": ["region_ocr"]},
        }
    )

    assert result.meets_threshold is True
    assert "intermediate_codes_missing" not in result.reasons
    assert "dimensions_partial" not in result.reasons


def test_extraction_confidence_meets_threshold_with_title_block_and_clean_checklist():
    result = ChatDrawingExtractionConfidenceService.evaluate(
        pdf_extract={
            "productCode": "90260140",
            "legible": True,
            "documentVision": {
                "legibilityScore": 0.98,
                "hasTitleBlock": True,
                "stages": ["region_ocr"],
            },
            "validationScopes": {"bom": {"available": True}},
        },
        items=[
            {
                "templateKey": "bom_match_ok",
                "status": "ok",
            }
        ],
    )

    assert result.meets_threshold is True
    assert result.score_percent >= 95
