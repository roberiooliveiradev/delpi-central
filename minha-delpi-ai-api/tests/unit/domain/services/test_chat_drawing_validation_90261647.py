"""Regressão — desenho 90261647 (OCR regional incompleto × índice do anexo)."""

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90261647() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50222447",
                    "description": "CA18VDAR-00986/06/06-9800-2100",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080110", "quantity": 1.0, "unit": "PC"},
                        {"code": "10420256", "quantity": 1.0, "unit": "PC"},
                    ],
                }
            ]
        }
    }


def _attachment_index_parse_90261647() -> dict:
    return {
        "productCode": "90261647",
        "revision": "73",
        "legible": True,
        "charCount": 1200,
        "componentCodes": ["10080110", "10420256", "50222447"],
        "intermediateCodes": ["50222447"],
        "fullText": """
QTD CODIGO
1 10080110 TERMINAL
1 10420256 CONECTOR
50222447
90261647
""",
        "validationScopes": {
            "bom": {"sourceKey": None, "available": False, "charCount": 0},
        },
    }


def _partial_regional_vision_90261647() -> dict:
    return {
        "productCode": "90261647",
        "revision": "73",
        "legible": True,
        "charCount": 2000,
        "componentCodes": [],
        "intermediateCodes": [],
        "bomRows": [],
        "bomSource": "bom_region",
        "validationScopes": {
            "bom": {
                "sourceKey": "bom_region",
                "available": True,
                "charCount": 40,
            },
        },
        "engine": "fitz_embedded",
        "stages": ["fitz_embedded", "region_ocr"],
        "schemaVersion": "1.0",
    }


def test_90261647_empty_regional_vision_keeps_attachment_bom_codes():
    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        _attachment_index_parse_90261647(),
        _partial_regional_vision_90261647(),
    )

    assert set(merged.get("componentCodes") or []) >= {"10080110", "10420256"}


def test_90261647_no_false_bom_missing_when_attachment_has_codes():
    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        _attachment_index_parse_90261647(),
        _partial_regional_vision_90261647(),
    )

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261647(),
        pdf_extract=merged,
        product_code="90261647",
    )

    bom_missing = [
        item
        for item in items
        if item.get("section") == "BOM"
        and "ausente no PDF" in str(item.get("item") or "")
    ]

    assert not bom_missing
