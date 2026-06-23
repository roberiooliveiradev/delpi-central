"""Camada assertiva — demote divergências PDF quando confiança < 95%."""

from app.domain.services.chat_drawing_validation_assertion_service import (
    ChatDrawingValidationAssertionService,
)


def test_assertion_demotes_pdf_conflicts_but_keeps_api_authoritative():
    items = [
        {
            "templateKey": "guide_structure_extra",
            "section": "Roteiro",
            "item": "Produto no roteiro fora da estrutura",
            "status": "critical_error",
            "pdfEvidence": "—",
            "apiEvidence": "90350413",
            "rule": "roteiro",
            "recommendation": "Remover",
        },
        {
            "templateKey": "bom_extra_item",
            "section": "BOM",
            "item": "Componente 10440154 extra no PDF",
            "status": "critical_error",
            "pdfEvidence": "10440154",
            "apiEvidence": "—",
            "rule": "bom",
            "recommendation": "Remover",
        },
    ]

    adjusted, confidence = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract={
            "productCode": "90264227",
            "legible": True,
            "documentVision": {
                "legibilityScore": 1.0,
                "hasTitleBlock": False,
                "stages": ["fitz_embedded", "region_ocr"],
            },
            "validationScopes": {"bom": {"available": True}},
        },
    )

    assert confidence is not None
    assert confidence.meets_threshold is False

    guide = next(
        item for item in adjusted if item.get("templateKey") == "guide_structure_extra"
    )
    bom = next(item for item in adjusted if item.get("templateKey") == "bom_extra_item")

    assert guide["status"] == "critical_error"
    assert bom["status"] == "pending"
    assert bom.get("validationLayer", {}).get("gate") == "extraction_confidence"

    confidence_item = next(
        item for item in adjusted if item.get("templateKey") == "extraction_confidence"
    )
    assert confidence_item["status"] == "pending"


def test_assertion_demotes_total_length_when_low_confidence():
    items = [
        {
            "templateKey": "total_length",
            "section": "Cotas",
            "item": "Comprimento total",
            "status": "critical_error",
            "pdfEvidence": "1.0 mm (PDF)",
            "apiEvidence": "660.0 mm (SG1010)",
            "rule": "total",
            "recommendation": "Corrigir",
        }
    ]

    adjusted, confidence = ChatDrawingValidationAssertionService.apply(
        items=items,
        pdf_extract={
            "productCode": "90260027",
            "legible": True,
            "documentVision": {
                "legibilityScore": 0.4,
                "hasTitleBlock": True,
                "stages": ["fitz_embedded"],
            },
            "validationScopes": {
                "dimensions": {"available": False, "sourceKey": "unavailable"}
            },
            "dimensions": {"totalLengthMm": 1.0},
        },
    )

    total_length = adjusted[1]

    assert confidence is not None
    assert confidence.meets_threshold is False
    assert total_length["status"] == "pending"
    assert total_length.get("validationLayer", {}).get("gate") == "extraction_confidence"
