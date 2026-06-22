"""Regressão — desenho 90264243 (BOM colunar lido; falso bom_missing/balloon por gate 75%)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_balloon_validation_service import (
    ChatDrawingBalloonValidationService,
)
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_assertion_service import (
    ChatDrawingValidationAssertionService,
)

configure_domain_infrastructure_ports()


def _payload_90264243() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "10080308",
                    "quantity": 1000.0,
                    "unit": "PC",
                    "components": [],
                },
                {
                    "code": "10080843",
                    "quantity": 1000.0,
                    "unit": "PC",
                    "components": [],
                },
                {
                    "code": "10130006",
                    "quantity": 30.0,
                    "unit": "MT",
                    "components": [],
                },
                {
                    "code": "10420396",
                    "quantity": 1.0,
                    "unit": "PC",
                    "components": [],
                },
            ]
        }
    }


def _pdf_extract_90264243() -> dict:
    return {
        "productCode": "90264243",
        "legible": True,
        "charCount": 912,
        "componentCodes": ["10080308", "10080843", "10130006", "10420396"],
        "intermediateCodes": [],
        "validationScopes": {
            "bom": {"sourceKey": "bom_region", "available": True, "charCount": 912},
            "stamp": {"sourceKey": "stamp_region", "available": True, "charCount": 3},
            "dimensions": {
                "sourceKey": "dimensions_region",
                "available": True,
                "charCount": 155,
            },
        },
        "dimensions": {
            "leftDecapeMm": 8.0,
            "rightDecapeMm": 15.0,
        },
        "bomRows": [
            {
                "code": "10080308",
                "quantity": "1000",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
            {
                "code": "10080843",
                "quantity": "1000",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
            {
                "code": "10130006",
                "quantity": "30",
                "quantitySource": "column_inferred",
                "quantityTrusted": False,
            },
            {
                "code": "10420396",
                "quantity": "1",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
        ],
        "bomVisionRefinement": {"columnRowCount": 4, "attempted": True},
        "sourceMetadata": {"stages": ["fitz_embedded", "region_ocr"]},
    }


def test_90264243_structured_bom_includes_untrusted_row_via_component_codes():
    comparison = ChatDrawingBomComparisonService.compare(
        root=_payload_90264243(),
        pdf_extract=_pdf_extract_90264243(),
        product_code="90264243",
    )

    assert "10130006" not in comparison.missing_in_pdf
    assert not comparison.missing_in_pdf


def test_90264243_no_false_bom_missing_in_checklist():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264243(),
        pdf_extract=_pdf_extract_90264243(),
        product_code="90264243",
    )

    bom_missing = [
        item
        for item in items
        if item.get("templateKey") == "bom_missing"
    ]

    assert not bom_missing


def test_90264243_balloon_ok_when_codes_in_structured_bom_table():
    items = ChatDrawingBalloonValidationService.build_check_items(
        pdf_extract=_pdf_extract_90264243(),
    )

    assert any(item.get("templateKey") == "balloon_presence_ok" for item in items)
    assert not any(item.get("templateKey") == "balloon_missing_codes" for item in items)


def test_90264243_extraction_confidence_meets_threshold_for_flat_mp_bom():
    result = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
        pdf_extract=_pdf_extract_90264243(),
    )

    assert result.meets_threshold is True
    assert result.score_percent >= 95
    assert "intermediate_codes_missing" not in result.reasons
    assert "dimensions_partial" not in result.reasons


def test_90264243_confidence_gate_does_not_demote_bom_checks():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264243(),
        pdf_extract=_pdf_extract_90264243(),
        product_code="90264243",
    )

    adjusted, confidence = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract=_pdf_extract_90264243(),
    )

    assert confidence is not None
    assert confidence.meets_threshold is True

    bom_missing = [
        item for item in adjusted if item.get("templateKey") == "bom_missing"
    ]
    balloon_missing = [
        item for item in adjusted if item.get("templateKey") == "balloon_missing_codes"
    ]
    confidence_item = next(
        item for item in adjusted if item.get("templateKey") == "extraction_confidence"
    )

    assert not bom_missing
    assert not balloon_missing
    assert confidence_item["status"] == "ok"
