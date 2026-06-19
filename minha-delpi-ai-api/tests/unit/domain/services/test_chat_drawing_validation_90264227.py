"""Regressão — desenho 90264227 (FLEXTRONICS chicote TRR-ITCC-0039)."""

from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from tests.unit.domain.services.test_chat_drawing_bom_comparison_service import (
    _payload_90264227,
)


def _pdf_extract_ocr() -> dict:
    return {
        "productCode": "90264227",
        "revision": "21",
        "internalRevision": "02",
        "legible": True,
        "componentCodes": [
            "10081867",
            "40091640",
            "1013091",
            "10140027",
            "50215425",
            "10440133",
            "50215426",
            "10440134",
            "50215433",
        ],
        "intermediateCodes": ["50215425", "50215426", "50215433"],
        "dimensions": {
            "leftDecapeMm": 6.0,
            "rightDecapeMm": 6.0,
            "totalLengthMm": 162.0,
            "segmentLengthsMm": [140.0, 150.0, 136.0, 162.0],
        },
    }


def test_90264227_no_false_bom_extra_for_child_cables():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264227(),
        pdf_extract=_pdf_extract_ocr(),
        product_code="90264227",
    )

    assert not any(
        item.get("item") == "Componente extra no PDF"
        and "10440133" in str(item.get("pdfEvidence"))
        for item in items
    )


def test_90264227_flags_missing_intermediate_50215434():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264227(),
        pdf_extract=_pdf_extract_ocr(),
        product_code="90264227",
    )

    assert any(
        item.get("item") == "Intermediário ausente no PDF"
        and "50215434" in str(item.get("apiEvidence"))
        for item in items
    )


def test_90264227_guide_not_aligned_with_structure():
    payload = {
        "product": {"code": "90264227", "description": "CHICOTE TRR-ITCC-0039"},
        **_payload_90264227(),
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90264227",
        payload=payload,
        has_pdf_attachment=False,
        api_ok=True,
    )

    items = package["drawingAnalysis"]["items"]

    assert any(
        item.get("item") == "Produto no roteiro fora da estrutura"
        and item.get("status") == "critical_error"
        for item in items
    )
    assert any(
        item.get("item") == "Produto da estrutura sem roteiro"
        and "50215434" in str(item.get("apiEvidence"))
        for item in items
    )


def test_90264227_revision_client_vs_internal_ok():
    payload = {
        "product": {
            "code": "90264227",
            "description": "CHICOTE TRR-ITCC-0039",
            "current_revision": "002",
            "last_revision_date": "20260617",
        },
        "structure": _payload_90264227()["structure"],
        "guide": {"items": [], "total": 0},
        "inspection": {"items": []},
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90264227",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract_ocr(),
    )

    revision_items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("item") == "Revisão"
    ]

    assert revision_items
    assert revision_items[0]["status"] == "ok"


def _pdf_extract_low_confidence() -> dict:
    return {
        **_pdf_extract_ocr(),
        "documentVision": {
            "legibilityScore": 1.0,
            "hasTitleBlock": False,
            "stages": ["fitz_embedded", "pypdf", "region_ocr"],
        },
        "validationScopes": {"bom": {"available": True}},
    }


def test_90264227_low_confidence_demotes_pdf_bom_but_keeps_guide_critical():
    payload = {
        "product": {
            "code": "90264227",
            "description": "CHICOTE TRR-ITCC-0039",
            "current_revision": "002",
            "last_revision_date": "20260617",
        },
        **_payload_90264227(),
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90264227",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract_low_confidence(),
    )

    analysis = package["drawingAnalysis"]
    layers = analysis.get("validationLayers") or {}
    confidence = layers.get("extractionConfidence") or {}

    assert confidence.get("meetsThreshold") is False
    assert confidence.get("thresholdPercent") == 95
    assert confidence.get("scorePercent", 100) < 95

    assert any(
        item.get("templateKey") == "extraction_confidence"
        and item.get("status") == "pending"
        for item in analysis["items"]
    )

    assert any(
        item.get("item") == "Produto no roteiro fora da estrutura"
        and item.get("status") == "critical_error"
        for item in analysis["items"]
    )

    bom_critical = [
        item
        for item in analysis["items"]
        if item.get("templateKey") in {"bom_extra", "bom_extra_item", "bom_quantity_mismatch"}
        and item.get("status") == "critical_error"
    ]
    assert not bom_critical

    assert analysis["status"] != "rejected" or analysis["criticalErrors"] == sum(
        1
        for item in analysis["items"]
        if item.get("status") == "critical_error"
    )
