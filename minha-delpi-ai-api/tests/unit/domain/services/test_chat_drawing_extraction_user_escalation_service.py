"""Escalação ao usuário só após OCR + LLM esgotados."""

from app.domain.services.chat_drawing_extraction_user_escalation_service import (
    ChatDrawingExtractionUserEscalationService,
)
from app.domain.services.chat_drawing_validation_assertion_service import (
    ChatDrawingValidationAssertionService,
)
from app.domain.services.chat_drawing_ambiguity_intelligence_service import (
    ChatDrawingAmbiguityIntelligenceService,
)


def test_escalation_blocked_before_llm_attempt():
    assert (
        ChatDrawingExtractionUserEscalationService.allows_user_escalation(
            pdf_extract={},
            meets_threshold=False,
        )
        is False
    )


def test_escalation_allowed_after_llm_failed():
    assert (
        ChatDrawingExtractionUserEscalationService.allows_user_escalation(
            pdf_extract={
                "extractionQualityRetry": {
                    "llmSolve": {"attempted": True, "resolved": False},
                },
            },
            meets_threshold=False,
        )
        is True
    )


def test_escalation_blocked_when_llm_resolved():
    assert (
        ChatDrawingExtractionUserEscalationService.allows_user_escalation(
            pdf_extract={
                "extractionQualityRetry": {
                    "llmSolve": {"attempted": True, "resolved": True},
                },
            },
            meets_threshold=False,
        )
        is False
    )


def test_assertion_does_not_pending_before_llm():
    items = [
        {
            "templateKey": "bom_extra_item",
            "section": "BOM",
            "item": "extra",
            "status": "critical_error",
            "pdfEvidence": "10440154",
            "apiEvidence": "—",
            "rule": "bom",
            "recommendation": "Remover",
        }
    ]

    adjusted, confidence = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract={
            "productCode": "90264227",
            "legible": True,
            "documentVision": {
                "legibilityScore": 1.0,
                "hasTitleBlock": False,
                "stages": ["fitz_embedded"],
            },
            "validationScopes": {"bom": {"available": True}},
        },
    )

    assert confidence is not None
    assert confidence.meets_threshold is False

    bom = next(item for item in adjusted if item.get("templateKey") == "bom_extra_item")
    confidence_item = next(
        item for item in adjusted if item.get("templateKey") == "extraction_confidence"
    )

    assert bom["status"] == "critical_error"
    assert confidence_item["status"] == "ok"
    assert confidence_item.get("extractionConfidence", {}).get("userEscalationAllowed") is False


def test_assertion_pending_after_llm_uses_after_llm_copy():
    items = [
        {
            "templateKey": "bom_extra_item",
            "section": "BOM",
            "item": "extra",
            "status": "critical_error",
            "pdfEvidence": "10440154",
            "apiEvidence": "—",
            "rule": "bom",
            "recommendation": "Remover",
        }
    ]

    adjusted, _ = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract={
            "productCode": "90264227",
            "legible": True,
            "documentVision": {
                "legibilityScore": 1.0,
                "hasTitleBlock": False,
                "stages": ["fitz_embedded"],
            },
            "validationScopes": {"bom": {"available": True}},
            "extractionQualityRetry": {
                "llmSolve": {"attempted": True, "resolved": False},
            },
        },
    )

    confidence_item = next(
        item for item in adjusted if item.get("templateKey") == "extraction_confidence"
    )
    bom = next(item for item in adjusted if item.get("templateKey") == "bom_extra_item")

    assert confidence_item["status"] == "pending"
    assert "visão" in str(confidence_item.get("recommendation") or "").lower()
    assert bom["status"] == "pending"


def test_ambiguity_skips_low_confidence_signal_before_llm():
    signals = ChatDrawingAmbiguityIntelligenceService.collect_signals(
        items=[],
        pdf_extract={},
        extraction_confidence={
            "meetsThreshold": False,
            "scorePercent": 70,
            "thresholdPercent": 95,
        },
    )

    assert not any(
        signal.get("detectorId") == "extraction_below_threshold" for signal in signals
    )
