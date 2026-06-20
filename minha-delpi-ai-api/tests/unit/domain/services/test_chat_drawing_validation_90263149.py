"""Regressão — desenho 90263149 (OCR confunde QTD com medidas da descrição)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_dimensions_extraction_service import (
    ChatDrawingDimensionsExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()


def _payload_90263149() -> dict:
    return {
        "product": {
            "code": "90263149",
            "type": "PA",
            "unit": "MI",
            "description": "CHICOTE DE LIGAÇÃO",
        },
        "structure": {
            "items": [
                {
                    "code": "10080010",
                    "quantity": 1000.0,
                    "unit": "PC",
                    "description": "TERM. LINGUETA 6,30X0,80",
                    "components": [],
                },
                {
                    "code": "10080044",
                    "quantity": 2000.0,
                    "unit": "PC",
                    "description": "TERM. FASTON 2,80X0,50",
                    "components": [],
                },
                {
                    "code": "10090050",
                    "quantity": 1000.0,
                    "unit": "PC",
                    "description": "ISOLADOR NYLON RETO 6,35 NU",
                    "components": [],
                },
                {
                    "code": "10140155",
                    "quantity": 1000.0,
                    "unit": "PC",
                    "description": "CHAVE HH 10A 6 PINOS",
                    "components": [],
                },
                {
                    "code": "10500020",
                    "quantity": 2000.0,
                    "unit": "PC",
                    "description": "TERMOENCOLHIVEL 3,20X0,40",
                    "components": [],
                },
                {
                    "code": "10500075",
                    "quantity": 2000.0,
                    "unit": "PC",
                    "description": "TERMOENCOLHIVEL 4,80X0,60",
                    "components": [],
                },
                {
                    "code": "50212969",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA22VERD-00120/05/06-0000-0000",
                    "components": [],
                },
                {
                    "code": "50232599",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA22VERD-00532/05/06-4400-6345",
                    "components": [],
                },
                {
                    "code": "50232600",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA22VERD-00145/06/06-0000-6345",
                    "components": [],
                },
                {
                    "code": "50223830",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "description": "CA22BRAN-00325/04/05-0600-4400",
                    "components": [
                        {"code": "10080044", "description": "TERM. FASTON"},
                    ],
                },
            ]
        },
        "guide": {
            "items": [
                {"product_code": "90263149", "bom_level": 0},
                {"product_code": "50212969", "bom_level": 1},
                {"product_code": "50232599", "bom_level": 1},
                {"product_code": "50232600", "bom_level": 1},
                {"product_code": "50223830", "bom_level": 1},
            ]
        },
        "inspection": {
            "items": [
                {
                    "product": "90263149",
                    "measurable_tests": [{"test_code": "506", "nominal": "500"}],
                    "textual_tests": [{"test_code": "001"}],
                }
            ]
        },
    }


def _ocr_noisy_pdf_extract_90263149() -> dict:
    return {
        "legible": True,
        "productCode": "90263149",
        "componentCodes": [
            "10080010",
            "10080044",
            "10090050",
            "10140155",
            "10500020",
            "10500075",
            "50212969",
            "50223830",
            "50232599",
            "50232600",
        ],
        "bomRows": [
            {
                "code": "10080010",
                "quantity": "6.",
                "description": "30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO CURTO UL ROHS",
            },
            {
                "code": "10080044",
                "quantity": "2.",
                "description": "80X0,50 0,50-1,65MM2 NU S/ISOLACAO FITADO ROHS UL",
            },
            {
                "code": "10090050",
                "quantity": "6.35",
                "description": "NU UL94V-2",
            },
            {
                "code": "10140155",
                "quantity": "6",
                "description": "PINOS GRAVACAO 127/220 2 PINOS JAMPEADA",
            },
            {
                "code": "10500020",
                "quantity": "3.",
                "description": "20X0,40 1/8POL (1,6) PT 125°C POLIOLEFINA COMP 33MM UL-ROHS",
            },
            {
                "code": "10500075",
                "quantity": "4.",
                "description": "80X0,60 3/16POL (2,4) PT 125°C POLIOLEFINA COMP 33MM ROHS",
            },
            {
                "code": "50212969",
                "quantity": "00120",
                "description": "/05/06-0000-0000 10020175 |CABO PVC",
            },
            {
                "code": "10080044",
                "quantity": "1",
                "description": "TERM. FASTON 2,80X0,50",
            },
        ],
        "validationScopes": {
            "bom": {"sourceKey": "bom_region", "available": True, "charCount": 2454},
        },
        "dimensions": ChatDrawingDimensionsExtractionService.extract_dimensions(
            "532±3\n325±3\n120±3\n345±3"
        ),
        "fullText": "532±3\n325±3\n120±3\n345±3",
    }


def _trusted_pdf_extract_90263149() -> dict:
    extract = _ocr_noisy_pdf_extract_90263149()
    extract["bomRows"] = [
        {"code": "10080010", "quantity": "1", "description": "TERM. LINGUETA 6,30X0,80"},
        {"code": "10080044", "quantity": "2", "description": "TERM. FASTON 2,80X0,50"},
        {"code": "10090050", "quantity": "1", "description": "ISOLADOR NYLON RETO 6,35 NU"},
        {"code": "10140155", "quantity": "1", "description": "CHAVE HH 10A 6 PINOS"},
        {"code": "10500020", "quantity": "2", "description": "TERMOENCOLHIVEL 3,20X0,40"},
        {"code": "10500075", "quantity": "2", "description": "TERMOENCOLHIVEL 4,80X0,60"},
        {"code": "50212969", "quantity": "1", "description": "CA22VERD-00120/05/06-0000-0000"},
    ]
    return extract


def test_90263149_ocr_noisy_quantities_not_critical_mismatch():
    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=_payload_90263149(),
        pdf_extract=_ocr_noisy_pdf_extract_90263149(),
        product_code="90263149",
    )

    assert not mismatches


def test_90263149_ocr_noisy_bom_missing_false_positive_for_pi_child():
    result = ChatDrawingBomComparisonService.compare(
        root=_payload_90263149(),
        pdf_extract=_ocr_noisy_pdf_extract_90263149(),
        product_code="90263149",
    )

    assert "10080044" not in result.missing_in_pdf


def test_90263149_trusted_quantities_match_api():
    trusted = ChatDrawingBomQuantityAssertivenessService.collect_trusted_quantities(
        root=_payload_90263149(),
        pdf_extract=_trusted_pdf_extract_90263149(),
        product_code="90263149",
    )

    assert trusted["10080010"] == 1.0
    assert trusted["10080044"] == 2.0
    assert trusted["50212969"] == 1.0


def test_90263149_validation_package_not_rejected_on_ocr_noise():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90263149",
        payload=_payload_90263149(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_ocr_noisy_pdf_extract_90263149(),
    )
    analysis = package.get("drawingAnalysis") or {}

    assert analysis.get("status") in {"approved", "approved_with_notes"}
    assert int(analysis.get("criticalErrors") or 0) == 0

    critical_qty = [
        item
        for item in analysis.get("items") or []
        if item.get("templateKey") == "bom_quantity_mismatch"
        and item.get("status") == "critical_error"
    ]

    assert not critical_qty


def test_90263149_length_tolerance_not_decape():
    dimensions = ChatDrawingDimensionsExtractionService.extract_dimensions(
        "532±3\n325±3\n120±3\n345±3"
    )

    assert dimensions.get("leftDecapeMm") is None


def test_90263149_decape_mismatch_not_error_when_only_length_tolerance():
    pdf_extract = {
        **_ocr_noisy_pdf_extract_90263149(),
        "dimensions": ChatDrawingDimensionsExtractionService.extract_dimensions(
            "532±3\n325±3\n120±3"
        ),
    }
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263149(),
        pdf_extract=pdf_extract,
        product_code="90263149",
    )

    decape_errors = [
        item
        for item in items
        if item.get("templateKey") == "decape_mismatch"
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not decape_errors


def test_90263149_column_table_resolves_description_quantity_noise():
    from app.application.services.chat_drawing_bom_vision_refinement_service import (
        ChatDrawingBomVisionRefinementService,
    )

    table = {
        "tableId": "region_bom_p0",
        "sourceRegion": "bom",
        "columns": [
            {"index": 0, "headerText": "POS"},
            {"index": 1, "headerText": "CÓDIGO"},
            {"index": 2, "headerText": "QTD"},
            {"index": 3, "headerText": "DESCRIÇÃO"},
        ],
        "rows": [
            {
                "index": 0,
                "cells": [
                    {"col": 0, "text": "1"},
                    {"col": 1, "text": "10090050"},
                    {"col": 2, "text": "1"},
                    {"col": 3, "text": "ISOLADOR NYLON RETO 6,35 NU UL94V-2"},
                ],
            }
        ],
    }
    pdf_extract = {
        **_ocr_noisy_pdf_extract_90263149(),
        "sourceMetadata": {"structuredTables": [table]},
    }
    refined = ChatDrawingBomVisionRefinementService.apply(
        pdf_extract,
        analyser_root=_payload_90263149(),
        product_code="90263149",
    )
    by_code = {
        row["code"]: row for row in refined.get("bomRows") or [] if isinstance(row, dict)
    }

    assert by_code["10090050"]["quantity"] == "1"
    assert by_code["10090050"]["quantitySource"] == "column"

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90263149",
        payload=_payload_90263149(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=refined,
    )
    analysis = package.get("drawingAnalysis") or {}

    assert int(analysis.get("criticalErrors") or 0) == 0
