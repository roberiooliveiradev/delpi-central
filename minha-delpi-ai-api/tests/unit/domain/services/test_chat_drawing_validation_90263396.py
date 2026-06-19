"""Regressão — desenho 90263396 (OCR parcial; cabo MT; PI por descrição)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90263396() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50233301",
                    "description": "CB20AZUL-00240/11/06",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080063", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10380013", "quantity": 240.0, "unit": "MT"},
                    ],
                },
                {
                    "code": "50233302",
                    "description": "CB20BRAN-00240/11/06",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080063", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10380063", "quantity": 240.0, "unit": "MT"},
                    ],
                },
                {
                    "code": "50233303",
                    "description": "CB20AMAR-00240/11/06",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080063", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10380055", "quantity": 240.0, "unit": "MT"},
                    ],
                },
                {
                    "code": "50233304",
                    "description": "CB20LARA-00238/11/06",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080063", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10380053", "quantity": 238.0, "unit": "MT"},
                    ],
                },
            ]
        }
    }


def _pdf_extract_90263396() -> dict:
    return {
        "legible": True,
        "componentCodes": [
            "10080063",
            "50233301",
            "10380013",
            "10090014",
        ],
        "intermediateCodes": ["50233301"],
        "fullText": (
            "CB20AZUL-00240/11/06 "
            "CB20BRAN-00240/11/06 "
            "CB20AMAR-00240/11/06 "
            "CB20LARA-00238/11/06"
        ),
        "dimensions": {},
    }


def test_90263396_no_intermediate_length_errors_when_cable_is_mt():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263396(),
        pdf_extract=_pdf_extract_90263396(),
        product_code="90263396",
    )

    length_errors = [
        item
        for item in items
        if item.get("status") == "critical_error"
        and "Comprimento" in str(item.get("item", ""))
    ]

    assert not length_errors


def test_90263396_intermediates_matched_by_description_not_marked_missing():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263396(),
        pdf_extract=_pdf_extract_90263396(),
        product_code="90263396",
    )

    missing_items = [
        item
        for item in items
        if "Intermediário" in str(item.get("item", ""))
        and item.get("status") in {"error", "critical_error"}
    ]

    assert not missing_items

    assert any(
        item.get("item") == "Intermediários" and item.get("status") == "ok"
        for item in items
    )
