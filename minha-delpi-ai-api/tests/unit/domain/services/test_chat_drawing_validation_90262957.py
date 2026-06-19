"""Regressão — desenho 90262957 (decape direito 10 mm; esquerdo só na descrição 50xx)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90262957() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50232502",
                    "description": "CA26MRBN-01127/06/10-0945-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10020043", "quantity": 1127.0}],
                },
                {
                    "code": "50232503",
                    "description": "CA26MRBN-01127/06/10-0945-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10020046", "quantity": 1127.0}],
                },
                {
                    "code": "50232504",
                    "description": "CA26PRET-01127/06/10-0945-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10020048", "quantity": 1127.0}],
                },
                {
                    "code": "50232505",
                    "description": "CA26PRET-01127/06/10-0945-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10020008", "quantity": 1127.0}],
                },
            ]
        }
    }


def _pdf_extract_90262957() -> dict:
    return {
        "legible": True,
        "componentCodes": [
            "50232502",
            "50232503",
            "50232504",
            "50232505",
        ],
        "intermediateCodes": [
            "50232502",
            "50232503",
            "50232504",
            "50232505",
        ],
        "dimensions": {
            "leftDecapeMm": None,
            "rightDecapeMm": 10.0,
            "totalLengthMm": 1127.0,
            "segmentLengthsMm": [1127.0, 1127.0, 1127.0, 1127.0],
            "cotaDecapeValuesMm": [10.0],
            "decapeIndication": {"left": False, "right": True},
        },
    }


def test_90262957_skips_left_decape_when_not_indicated_on_drawing():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90262957(),
        pdf_extract=_pdf_extract_90262957(),
        product_code="90262957",
    )

    decape_errors = [
        item
        for item in items
        if str(item.get("item", "")).startswith("Decape")
        and item.get("status") == "error"
    ]

    assert not any("esquerdo" in str(item.get("item", "")).lower() for item in decape_errors)
    assert not any("50232502" in str(item.get("item", "")) for item in decape_errors)


def test_90262957_right_decape_matches_intermediate_description():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90262957(),
        pdf_extract=_pdf_extract_90262957(),
        product_code="90262957",
    )

    assert not any(
        "Decape direito" in str(item.get("item", "")) and item.get("status") == "error"
        for item in items
    )
