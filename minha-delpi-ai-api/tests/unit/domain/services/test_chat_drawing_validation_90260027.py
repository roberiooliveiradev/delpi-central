"""Regressão — desenho 90260027 (chicote 660 mm; CA18 falso positivo 653; OCR ruim)."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_total_length_reference_service import (
    ChatDrawingTotalLengthReferenceService,
)
from app.domain.services.chat_drawing_validation_assertion_service import (
    ChatDrawingValidationAssertionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)


def _root_90260027() -> dict:
    return {
        "product": {
            "code": "90260027",
            "description": "CHICOTE PVC SINGELO 660MM",
            "unit": "MI",
        },
        "structure": {
            "items": [
                {
                    "code": "90260027",
                    "description": "CHICOTE PVC SINGELO 660MM",
                    "type": "PA",
                    "components": [
                        {
                            "code": "50220010",
                            "description": "CA18VDAR-00653/07/06-0000-2100",
                            "quantity": 1.0,
                            "components": [
                                {
                                    "code": "10020018",
                                    "quantity": 653.0,
                                    "unit": "MT",
                                    "description": "CABO PVC 105C 18AWG",
                                },
                            ],
                        }
                    ],
                }
            ]
        },
    }


def _pdf_extract_low_confidence() -> dict:
    return {
        "productCode": "90260027",
        "revision": "01",
        "legible": True,
        "componentCodes": ["50220010", "10020018", "10080021"],
        "intermediateCodes": ["50220010"],
        "validationScopes": {
            "dimensions": {
                "sourceKey": "unavailable",
                "available": False,
                "charCount": 0,
            },
            "bom": {
                "sourceKey": "stamp_bom_table",
                "available": True,
                "charCount": 80,
            },
        },
        "dimensions": {
            "totalLengthMm": 1.0,
            "segmentLengthsMm": [1.0],
            "leftDecapeMm": 7.0,
            "rightDecapeMm": 2.0,
            "decapeIndication": {"left": True, "right": True},
        },
        "documentVision": {
            "legibilityScore": 0.4,
            "hasTitleBlock": True,
            "stages": ["fitz_embedded"],
        },
    }


def test_90260027_total_length_reference_prefers_pa_description_mm():
    reference = ChatDrawingTotalLengthReferenceService.resolve(_root_90260027())

    assert reference is not None
    assert reference.length_mm == 660.0
    assert reference.unit_label == "mm"


def test_90260027_low_confidence_demotes_total_length_critical_to_pending():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_root_90260027(),
        pdf_extract=_pdf_extract_low_confidence(),
        product_code="90260027",
    )

    adjusted, confidence = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract=_pdf_extract_low_confidence(),
    )

    assert confidence is not None
    assert confidence.meets_threshold is False

    total_length = next(
        item for item in adjusted if item.get("templateKey") == "total_length"
    )

    assert total_length["status"] == "pending"
    assert "660" in str(total_length.get("apiEvidence") or "")
    assert "mm" in str(total_length.get("apiEvidence") or "").lower()


def test_90260027_report_includes_dimensions_comparison_section():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260027",
        payload=_root_90260027(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract_low_confidence(),
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert "Cotas × estrutura" in report
    assert "Comprimento total" in report
    assert "660" in report
    assert "Estrutura (SG1010)" in report
