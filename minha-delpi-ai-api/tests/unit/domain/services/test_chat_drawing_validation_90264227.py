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


def test_90264227_no_false_bom_extra_for_wire_gauge_ocr_row():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264227(),
        pdf_extract={
            "productCode": "90264227",
            "revision": "21",
            "legible": True,
            "componentCodes": [
                "10081867",
                "10091640",
                "10130091",
                "10140027",
                "50215425",
                "50215426",
                "50215433",
                "50215434",
                "10440133",
                "10440134",
            ],
            "intermediateCodes": ["50215425", "50215426", "50215433", "50215434"],
            "bomRows": [
                {
                    "code": "10061667",
                    "quantity": "2",
                    "description": "20ANG OURO ROHS (FLEXTRONIGS)",
                    "quantitySource": "refined_column",
                    "quantityTrusted": True,
                }
            ],
            "validationScopes": {
                "bom": {
                    "available": True,
                    "text": "20ANG OURO ROHS",
                    "sourceKey": "bom_region",
                }
            },
        },
        product_code="90264227",
    )

    assert not any(
        item.get("item") == "Componente extra no PDF"
        and "10061667" in str(item.get("pdfEvidence"))
        for item in items
    )


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


def test_90264227_high_extraction_confidence_keeps_bom_conflicts_visible():
    payload = {
        "product": {
            "code": "90264227",
            "description": "CHICOTE TRR-ITCC-0039",
            "current_revision": "002",
            "last_revision_date": "20260617",
        },
        **_payload_90264227(),
    }
    pdf_extract = {
        **_pdf_extract_ocr(),
        "charCount": 6000,
        "sourceMetadata": {"stages": ["region_ocr"]},
        "extractionQualityRetry": {
            "meetsTarget": True,
            "selectedConfidence": {
                "score": 0.96,
                "threshold": 0.95,
                "meetsThreshold": True,
                "components": {
                    "legibility": 0.96,
                    "stamp": 1.0,
                    "bom_scope": 1.0,
                    "ocr_regions": 1.0,
                    "bom_completeness": 1.0,
                    "dimensions": 1.0,
                },
                "reasons": [],
            },
        },
    }

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90264227",
        payload=payload,
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=pdf_extract,
    )

    analysis = package["drawingAnalysis"]
    confidence = (analysis.get("validationLayers") or {}).get("extractionConfidence") or {}

    assert confidence.get("meetsThreshold") is True
    assert confidence.get("scorePercent", 0) >= 95

    assert any(
        item.get("templateKey") == "extraction_confidence"
        and item.get("status") == "ok"
        for item in analysis["items"]
    )

    assert not any(
        item.get("templateKey") in {"bom_extra", "bom_extra_item", "bom_quantity_mismatch"}
        and item.get("status") == "pending"
        and (item.get("validationLayer") or {}).get("gate") == "extraction_confidence"
        for item in analysis["items"]
    )


def _pdf_extract_low_confidence() -> dict:
    return {
        "productCode": "90264227",
        "legible": True,
        "charCount": 80,
        "componentCodes": ["10440134", "50215426"],
        "sourceMetadata": {"stages": ["fitz_embedded"]},
        "validationScopes": {"bom": {"available": True}},
        "extractionQualityRetry": {
            "meetsTarget": False,
            "selectedConfidence": {
                "score": 0.48,
                "threshold": 0.95,
                "meetsThreshold": False,
                "scorePercent": 48,
                "components": {"legibility": 0.48},
                "reasons": ["component_codes_missing", "dimensions_missing"],
            },
        },
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
