"""Auto-detecção de ambiguidade — sinais, policies e ask-user."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_ambiguity_intelligence_service import (
    ChatDrawingAmbiguityIntelligenceService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_presentation_service import (
    ChatDrawingValidationPresentationService,
)

configure_domain_infrastructure_ports()


def test_ambiguity_intelligence_catalog_exists():
    kinds = ChatDrawingValidationContentService.get_node(
        "ambiguityIntelligence",
        "kinds",
    )
    detectors = ChatDrawingValidationContentService.get_node(
        "ambiguityIntelligence",
        "detectors",
    )

    assert isinstance(kinds, dict)
    assert "conflicting_notes" in kinds
    assert "low_confidence" in kinds
    assert isinstance(detectors, dict)
    assert "conflicting_dimension_notes" in detectors
    assert "extraction_below_threshold" in detectors


def test_conflicting_notes_signal_and_withhold():
    pdf_extract = {
        "dimensions": {
            "notesText": "TERMO ENCOLHÍVEL 25 MM DECAPE 14 MM",
            "leftDecapeMm": 5.0,
            "rightDecapeMm": 2.0,
        },
        "legible": True,
    }

    signals = ChatDrawingAmbiguityIntelligenceService.collect_signals(
        pdf_extract=pdf_extract,
        items=[],
    )

    assert any(
        signal.get("detectorId") == "conflicting_dimension_notes"
        for signal in signals
    )
    assert ChatDrawingAmbiguityIntelligenceService.should_withhold(
        "per_intermediate_decape",
        signals=signals,
    )


def test_apply_suppresses_decapes_ok_under_ambiguity():
    pdf_extract = {
        "dimensions": {
            "notesText": "TERMO ENCOLHÍVEL 25 MM DECAPE 14 MM PRE-DECAPE",
        }
    }
    items = [
        ChatDrawingValidationContentService.item_from_template(
            "dimension_note_ambiguous",
            status="pending",
            pdf_evidence="nota",
            api_evidence="—",
        ),
        ChatDrawingValidationContentService.item_from_template(
            "decapes_ed",
            status="ok",
            pdf_evidence="E=5; D=2",
            api_evidence="—",
            recommendation_field="recommendationOk",
        ),
    ]
    signals = ChatDrawingAmbiguityIntelligenceService.collect_signals(
        pdf_extract=pdf_extract,
        items=items,
    )
    adjusted, signals = ChatDrawingAmbiguityIntelligenceService.apply(
        items,
        signals,
        pdf_extract=pdf_extract,
    )

    note = next(
        item
        for item in adjusted
        if item.get("templateKey") == "dimension_note_ambiguous"
    )
    decapes = next(
        item for item in adjusted if item.get("templateKey") == "decapes_ed"
    )

    assert note.get("ambiguity")
    assert "confirmação" in str(note.get("recommendation") or "").lower()
    assert "Não afirmei" in str(note.get("recommendation") or "")
    assert decapes.get("status") == "not_applicable"
    assert decapes.get("ambiguitySuppressed") is True
    assert any(
        signal.get("detectorId") == "asserted_ok_under_ambiguity"
        for signal in signals
    )


def test_describe_nonconformity_uses_ask_user_envelope():
    item = ChatDrawingValidationContentService.item_from_template(
        "dimension_note_ambiguous",
        status="pending",
        pdf_evidence="nota",
        api_evidence="—",
    )
    item["ambiguity"] = {
        "kind": "conflicting_notes",
        "title": "sinais conflitantes no PDF",
        "whyEscalated": "mistura de notas.",
        "systemDidNot": "decape E automático",
        "askUser": "Confira no desenho.",
        "resolveHint": "Use o chip.",
    }

    detail = ChatDrawingValidationPresentationService.describe_nonconformity(item)

    assert "Preciso da sua confirmação" in detail
    assert "Não afirmei" in detail
    assert "Confira no desenho" in detail


def test_dimensions_table_omits_not_applicable_rows():
    package = {
        "analyserRoot": {},
        "drawingAnalysis": {
            "items": [
                ChatDrawingValidationContentService.item_from_template(
                    "dimension_note_ambiguous",
                    status="pending",
                    pdf_evidence="nota",
                    api_evidence="—",
                ),
                {
                    **ChatDrawingValidationContentService.item_from_template(
                        "decapes_ed",
                        status="not_applicable",
                        pdf_evidence="E=5",
                        api_evidence="—",
                    ),
                    "ambiguitySuppressed": True,
                },
            ]
        },
    }

    lines = ChatDrawingValidationPresentationService.format_dimensions_comparison_section(
        package
    )
    joined = "\n".join(lines)

    assert "confirmação" in joined.lower() or "nota dimensional" in joined.lower()
    assert "Decapes" not in joined


def test_low_confidence_signal_from_pending_extraction_item():
    items = [
        ChatDrawingValidationContentService.item_from_template(
            "extraction_confidence",
            status="pending",
            pdf_evidence="70%",
            api_evidence="—",
            recommendation_field="recommendationPending",
        )
    ]
    signals = ChatDrawingAmbiguityIntelligenceService.collect_signals(
        items=items,
        extraction_confidence={
            "meetsThreshold": False,
            "scorePercent": 70,
            "thresholdPercent": 95,
        },
    )
    adjusted, _ = ChatDrawingAmbiguityIntelligenceService.apply(items, signals)

    confidence = next(
        item
        for item in adjusted
        if item.get("templateKey") == "extraction_confidence"
    )

    assert any(
        signal.get("detectorId") == "extraction_below_threshold" for signal in signals
    )
    assert confidence.get("ambiguity")
    assert "confirmação" in str(confidence.get("recommendation") or "").lower()
