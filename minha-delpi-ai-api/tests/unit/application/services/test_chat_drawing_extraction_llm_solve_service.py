"""LLM/VLM solve após OCR abaixo do limiar."""

from unittest.mock import patch

from app.application.services.chat_drawing_extraction_llm_solve_service import (
    ChatDrawingExtractionLlmSolveService,
)


def _low_confidence_payload() -> dict:
    return {
        "productCode": "90264277",
        "legible": True,
        "fullText": "OCR parcial",
        "documentVision": {
            "legibilityScore": 0.5,
            "hasTitleBlock": False,
            "stages": ["region_ocr"],
        },
        "validationScopes": {"bom": {"available": False}},
        "sourceMetadata": {
            "stages": ["region_ocr"],
            "regionTexts": {"stamp": "parcial"},
        },
        "extractionQualityRetry": {
            "meetsTarget": False,
            "selectedConfidence": {
                "score": 0.5,
                "threshold": 0.95,
                "meetsThreshold": False,
                "scorePercent": 50,
            },
        },
    }


def test_llm_solve_skips_when_already_meets_target():
    payload = {
        "productCode": "90264277",
        "revision": "00",
        "legible": True,
        "charCount": 4974,
        "componentCodes": [
            "10080018",
            "10080158",
            "10380037",
            "50226055",
            "50226056",
            "50226057",
        ],
        "intermediateCodes": ["50226055", "50226056", "50226057"],
        "validationScopes": {
            "bom": {"available": True, "charCount": 1539},
            "dimensions": {"available": True, "charCount": 854},
            "stamp": {"available": True, "charCount": 32},
        },
        "dimensions": {"totalLengthMm": 1000.0},
        "documentVision": {
            "legibilityScore": 1.0,
            "hasTitleBlock": False,
            "stages": ["fitz_embedded", "pypdf", "region_ocr"],
        },
        "sourceMetadata": {"stages": ["fitz_embedded", "pypdf", "region_ocr"]},
        "extractionQualityRetry": {"meetsTarget": True},
    }

    result = ChatDrawingExtractionLlmSolveService.apply_if_needed(
        "/tmp/fake.pdf",
        filename="fake.pdf",
        pdf_extract=payload,
    )
    meta = (result.get("extractionQualityRetry") or {}).get("llmSolve") or {}

    assert meta.get("attempted") is False
    assert meta.get("resolved") is True
    assert meta.get("skippedReason") == "already_meets_target"


def test_llm_solve_marks_attempted_when_vlm_empty():
    with patch(
        "app.application.services.chat_document_vision.chat_document_vision_stage_service."
        "ChatDocumentVisionStageService.stage_ollama_vlm",
        return_value={"fullText": "", "warnings": ["vlm_no_images"]},
    ):
        result = ChatDrawingExtractionLlmSolveService.apply_if_needed(
            "/tmp/fake.pdf",
            filename="fake.pdf",
            pdf_extract=_low_confidence_payload(),
        )

    meta = (result.get("extractionQualityRetry") or {}).get("llmSolve") or {}

    assert meta.get("attempted") is True
    assert meta.get("resolved") is False
    assert meta.get("skippedReason") == "empty_or_unavailable"


def test_llm_solve_merges_vlm_text_and_reattaches_meta():
    high_text = (
        "PRODUTO 90264277 REV 02\n"
        "10440154 50215426 10020018 10080021\n"
        "COMPRIMENTO TOTAL 660 mm\n"
    )

    with patch(
        "app.application.services.chat_document_vision.chat_document_vision_stage_service."
        "ChatDocumentVisionStageService.stage_ollama_vlm",
        return_value={
            "fullText": high_text,
            "stampText": "90264277 REV 02",
            "bomText": "10440154 50215426 10020018",
            "regionTexts": {
                "stamp": "90264277 REV 02",
                "bom": "10440154 50215426 10020018",
                "dimensions": "COMPRIMENTO TOTAL 660 mm",
            },
            "vlmRegionsSent": ["stamp", "bom", "dimensions"],
            "vlmImageCount": 3,
            "warnings": [],
        },
    ):
        result = ChatDrawingExtractionLlmSolveService.apply_if_needed(
            "/tmp/fake.pdf",
            filename="fake.pdf",
            pdf_extract=_low_confidence_payload(),
        )

    meta = (result.get("extractionQualityRetry") or {}).get("llmSolve") or {}

    assert meta.get("attempted") is True
    assert "660" in str(result.get("fullText") or "")
    assert result.get("extractor") == "llm_solve_vlm"
    assert "scoreAfter" in meta
