"""Regressão — 90261823: ODA colado + OCR truncado não gera intermediate_missing/QTD lixo."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

configure_domain_infrastructure_ports()


def _payload_90261823() -> dict:
    return {
        "product": {"code": "90261823", "current_revision": "004"},
        "structure": {
            "items": [
                {
                    "code": "10350006",
                    "description": "ABRAÇADEIRA 3,6X150MM NATURAL - ROHS",
                    "quantity": 1000.0,
                    "unit": "MI",
                },
                {
                    "code": "10500017",
                    "description": "TUBO ISOLANTE 12,00X0,80 PT 130°C",
                    "quantity": 1000.0,
                    "unit": "MI",
                },
                {
                    "code": "50222629",
                    "description": "CA0,75BRAN-01005/14/06-0000-1100",
                    "quantity": 1.0,
                    "unit": "MI",
                    "components": [
                        {"code": "10020043", "quantity": 1005.0},
                        {"code": "10080111", "quantity": 1000.0},
                    ],
                },
                {
                    "code": "50231401",
                    "description": "CA0,75PRET-01005/14/06-0000-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
                {
                    "code": "50231402",
                    "description": "CA0,75AZUL-01005/14/06-0000-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
                {
                    "code": "50231403",
                    "description": "CA0,75VERM-01005/14/06-0000-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
                {
                    "code": "50231405",
                    "description": "CA0,75VDAR-01008/06/06-2100-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
                {
                    "code": "50231925",
                    "description": "CA0,75MRBN-00285/14/06-0000-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
                {
                    "code": "50231926",
                    "description": "CA0,75MARR-00285/14/06-0000-1145",
                    "quantity": 1.0,
                    "unit": "MI",
                },
            ]
        },
    }


def _pdf_extract_90261823() -> dict:
    """Simula leitura ODA: região BOM truncada + cadReference com códigos colados/completos."""
    return {
        "productCode": "90261823",
        "legible": True,
        "bomSource": "bom_region",
        "componentCodes": [
            "10350006",
            "50222629",
            "50231401",
            "50231402",
            "50231403",
            "10090045",
            "10500017",
            "10080111",
        ],
        "intermediateCodes": ["50222629", "50231401", "50231402", "50231403"],
        "bomRows": [
            {
                "code": "10350006",
                "quantity": "01",
                "description": "ABRAÇADEIRA T-30R",
                "quantitySource": "column_inferred",
                "quantityTrusted": True,
            },
            {
                "code": "50222629",
                "quantity": "30",
                "description": "CA0,75BRAN-01005/14/06-0000-1100",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            },
            {
                "code": "50231401",
                "quantity": None,
                "description": "CA0,75PRET-01005/14/06-0000-1145",
                "quantitySource": "column",
                "quantityTrusted": False,
            },
            {
                "code": "50231402",
                "quantity": None,
                "description": "CA0,75AZUL-01005/14/06-0000-1145",
                "quantitySource": "column",
                "quantityTrusted": False,
            },
            {
                "code": "50231403",
                "quantity": "81.0",
                "description": "CA0,75VERM-01005/14/06-0000-1145",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            },
            {
                "code": "10500017",
                "quantity": "0.7560051",
                "description": "fu",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            },
        ],
        "bomVisionRefinement": {"columnRowCount": 6, "resolved": 3},
        "sourceMetadata": {
            "cadReferenceText": (
                "50222629\nCA0,75BRAN-01005/14/06-0000-1100\n"
                "50231401\nCA0,75PRET-01005/14/06-0000-1145\n"
                "50231402\nCA0,75AZUL-01005/14/06-0000-1145\n"
                "50231403\nCA0,75VERM-01005/14/06-0000-1145\n"
                "50231925\nCA0,75MRBN-00285/14/06-0000-1145\n"
                "50231926\nCA0,75MARR-00285/14/06-0000-1145\n"
                "50231405\nCA0,75VDAR-01008/06/06-2100-1145\n"
                "10350006\n10500017\n"
            ),
            "dimensionsText": (
                "50231405 CA0,75VDAR-01008/06/06-2100-1145\n"
                "50231925 CA0,75MRBN-00285/14/06-0000-1145\n"
                "50231926 CA0,75MARR-00285/14/06-0000-1145\n"
            ),
        },
    }


def test_component_code_matches_oda_glued_to_description():
    glued = "50231405CA0,75VDAR-01008/06/06-2100-1145"
    matches = ChatDrawingPatternsService.component_code().findall(glued)

    assert "50231405" in matches


def test_90261823_resolve_intermediates_from_cad_haystack():
    resolved = ChatDrawingBomComparisonService.resolve_pdf_intermediate_codes(
        root=_payload_90261823(),
        pdf_extract=_pdf_extract_90261823(),
        product_code="90261823",
    )

    assert {"50231405", "50231925", "50231926"} <= resolved
    assert {"50222629", "50231401", "50231402", "50231403"} <= resolved


def test_90261823_no_false_intermediate_missing():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261823(),
        pdf_extract=_pdf_extract_90261823(),
        product_code="90261823",
    )
    missing = [
        item
        for item in items
        if item.get("templateKey") == "intermediate_missing"
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not missing


def test_90261823_ocr_garbage_quantities_do_not_create_pending():
    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=_payload_90261823(),
        pdf_extract=_pdf_extract_90261823(),
        product_code="90261823",
    )
    pending_codes = {item.code for item in pending}

    # QTD inventada pelo refined_column (30, 81, 0.756) — não vira pending.
    assert "50222629" not in pending_codes
    assert "50231403" not in pending_codes
    assert "10500017" not in pending_codes
    # 01 legítimo em MI pode permanecer pending (unidade não comparável) — ok.


def test_90261823_package_without_false_bom_errors():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261823",
        payload=_payload_90261823(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract=_pdf_extract_90261823(),
    )
    analysis = package.get("drawingAnalysis") or {}
    false_keys = {
        "intermediate_missing",
        "bom_quantity_mismatch",
        "bom_missing",
    }
    false_errors = [
        item
        for item in analysis.get("items") or []
        if item.get("templateKey") in false_keys
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not false_errors
