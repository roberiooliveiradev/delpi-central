"""Regressão — desenho 90261656 (referência WEG REF:/Z-0555 no índice do anexo)."""

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90261656() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50222456",
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


def _attachment_index_parse_90261656() -> dict:
    return {
        "productCode": "90261656",
        "revision": "73",
        "legible": True,
        "charCount": 800,
        "componentCodes": ["10056551", "10080110", "10420256", "50222456"],
        "intermediateCodes": ["50222456"],
        "fullText": """
REF:
Z-0555 REV:73
WEG INDUSTRIAS S.A.-MOTORES
10056551
90261656
""",
        "validationScopes": {
            "bom": {"sourceKey": None, "available": False, "charCount": 0},
        },
    }


def _regional_vision_90261656() -> dict:
    return {
        "productCode": "90261656",
        "revision": "73",
        "legible": True,
        "charCount": 2000,
        "componentCodes": ["10420256", "10080110"],
        "intermediateCodes": ["50222456"],
        "bomRows": [
            {"code": "10080110", "quantity": "1", "description": None},
            {"code": "10420256", "quantity": "1", "description": None},
        ],
        "bomSource": "bom_region",
        "validationScopes": {
            "bom": {
                "sourceKey": "bom_region",
                "available": True,
                "charCount": 180,
            },
            "dimensions": {
                "sourceKey": "dimensions_region",
                "available": True,
                "charCount": 40,
            },
        },
        "engine": "fitz_embedded",
        "stages": ["fitz_embedded", "region_ocr"],
        "schemaVersion": "1.0",
        "legibilityScore": 1.0,
        "durationMs": 10.0,
    }


def test_90261656_merge_drops_attachment_client_reference():
    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        _attachment_index_parse_90261656(),
        _regional_vision_90261656(),
    )

    assert "10056551" not in (merged.get("componentCodes") or [])
    assert set(merged.get("componentCodes") or []) == {"10420256", "10080110"}
    assert merged["validationScopes"]["bom"]["available"] is True
    assert merged["validationScopes"]["bom"]["sourceKey"] == "bom_region"


def test_90261656_no_false_bom_extra_after_merge():
    merged = ChatDocumentVisionService.merge_into_drawing_parse(
        _attachment_index_parse_90261656(),
        _regional_vision_90261656(),
    )

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261656(),
        pdf_extract=merged,
        product_code="90261656",
    )

    bom_errors = [
        item
        for item in items
        if item.get("section") == "BOM"
        and item.get("status") == "critical_error"
    ]

    assert not bom_errors

    assert any(
        item.get("item") == "Conjunto de componentes"
        and item.get("status") == "ok"
        for item in items
    )
