"""Regressão — desenho 90261757 (referência WEG DC:Z; PI qty=1 × cabo 136 MT)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90261757() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50222551",
                    "description": "CA0,75VDAR-00136/06/06-9800-2100",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020194", "quantity": 136.0, "unit": "MT"},
                        {"code": "10080021", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10080598", "quantity": 1000.0, "unit": "PC"},
                    ],
                }
            ]
        }
    }


def _pdf_extract_90261757() -> dict:
    return {
        "legible": True,
        "componentCodes": [
            "10080021",
            "10020194",
            "50222551",
            "10080598",
        ],
        "intermediateCodes": ["50222551"],
        "bomRows": [
            {
                "code": "10056570",
                "quantity": "855",
                "description": "REV: 15",
            },
            {"code": "10080021", "quantity": None, "description": None},
            {"code": "10020194", "quantity": None, "description": None},
            {"code": "50222551", "quantity": None, "description": None},
            {"code": "10080598", "quantity": None, "description": None},
        ],
        "sourceMetadata": {
            "stampText": "10056570 DC:Z-855 REV: 15\n90261757",
            "annotationText": "WEG INDUSTRIAS S.A- MOTORES\n10056570 DC:Z-855 REV: 15",
        },
        "validationScopes": {
            "bom": {
                "sourceKey": "stamp_bom_table",
                "available": True,
                "charCount": 120,
            },
            "dimensions": {
                "sourceKey": "dimensions_region",
                "available": True,
                "charCount": 5,
            },
        },
        "dimensions": {
            "totalLengthMm": 136.0,
            "leftDecapeMm": None,
            "rightDecapeMm": None,
            "segmentLengthsMm": [136.0],
            "decapeIndication": {"left": False, "right": False},
        },
    }


def test_90261757_client_reference_not_extra_bom():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261757(),
        pdf_extract=_pdf_extract_90261757(),
        product_code="90261757",
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
        and item.get("pdfScope")
        for item in items
    )


def test_90261757_total_length_matches_cable_not_piece_quantity():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261757(),
        pdf_extract=_pdf_extract_90261757(),
        product_code="90261757",
    )

    length_items = [
        item for item in items if item.get("item") == "Comprimento total"
    ]

    assert len(length_items) == 1
    assert length_items[0]["status"] == "ok"
    assert "136" in str(length_items[0].get("apiEvidence"))
    assert "1.0" not in str(length_items[0].get("apiEvidence"))
