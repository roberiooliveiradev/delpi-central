"""Regressão — 90261893: termoencolhível OCR não vira intermediate_extra."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90261893() -> dict:
    return {
        "product": {"code": "90261893", "current_revision": "002"},
        "structure": {
            "items": [
                {
                    "code": "50212382",
                    "description": "CA22AZUL-00423/10/03-0000-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50222736",
                    "description": "CA22AMAR-00417/04/10-0600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50222737",
                    "description": "CA22PRET-00397/04/10-0600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
                {
                    "code": "50222738",
                    "description": "CA22VERM-00417/04/10-0600-0000",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1.0,
                    "components": [],
                },
            ]
        },
        "guide": {"items": []},
        "inspection": {"items": []},
    }


def _pdf_extract_90261893() -> dict:
    return {
        "productCode": "90261893",
        "revision": "05",
        "internalRevision": "04",
        "legible": True,
        "titleBlock": {
            "rawText": "Do >\nRR\n—— a\nEB",
            "fields": {"rev": "05", "description": "CHICOTE DE LIGACAO"},
        },
        "intermediateCodes": [
            "50222736",
            "50222737",
            "50222738",
            "50250279",
        ],
        "bomRows": [
            {
                "code": "50222736",
                "description": "/10/04-0000-0600",
                "quantitySource": "column",
            },
            {
                "code": "50250279",
                "description": "LUVATERMOENCOLHVEL =",
                "quantitySource": "column",
                "quantityTrusted": False,
            },
        ],
    }


def test_90261893_drops_termoencolhivel_phantom_intermediate():
    resolved = ChatDrawingBomComparisonService.resolve_pdf_intermediate_codes(
        root=_payload_90261893(),
        pdf_extract=_pdf_extract_90261893(),
        product_code="90261893",
    )

    assert "50250279" not in resolved

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261893(),
        pdf_extract=_pdf_extract_90261893(),
        product_code="90261893",
    )

    extra = [
        item
        for item in items
        if item.get("templateKey") in {"intermediate_extra", "intermediate_extra_item"}
        and item.get("status") == "critical_error"
    ]

    assert not extra
