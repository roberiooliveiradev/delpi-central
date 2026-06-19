"""Regressão — desenho 90263954 (decape E/D por cota, MP alternativo = 10400111)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90263954() -> dict:
    return {
        "product": {"code": "90263954", "type": "PA", "unit": "MI"},
        "structure": {
            "items": [
                {
                    "code": "50233698",
                    "description": "CF20BRAN-00232/11/06-0000-6314",
                    "type": "PI",
                    "quantity": 1.0,
                    "unit": "MI",
                    "components": [
                        {
                            "code": "10400036",
                            "description": "CABO SIL 200°C 20AWG BN 600V STYLE 3135 = 10400111",
                        }
                    ],
                },
                {
                    "code": "50233699",
                    "description": "CF20PRET-00133/11/07-0000-0110",
                    "type": "PI",
                    "quantity": 1.0,
                    "unit": "MI",
                    "components": [{"code": "10400039", "description": "CABO SIL PT"}],
                },
                {
                    "code": "50233700",
                    "description": "CF20AZUL-00133/11/07-0000-0110",
                    "type": "PI",
                    "quantity": 1.0,
                    "unit": "MI",
                    "components": [{"code": "10400035", "description": "CABO SIL AL"}],
                },
                {
                    "code": "50233701",
                    "description": "CF20VERM-00214/06/03-6314-0000",
                    "type": "PI",
                    "quantity": 1.0,
                    "unit": "MI",
                    "components": [
                        {
                            "code": "10400040",
                            "description": "CABO SIL 200°C 20AWG VM 600V STYLE 3135 = 10400112",
                        }
                    ],
                },
            ]
        }
    }


def _pdf_extract_90263954() -> dict:
    return {
        "legible": True,
        "componentCodes": [
            "50233698",
            "50233699",
            "50233700",
            "50233701",
            "10400036",
            "10400111",
            "10400040",
            "10400112",
        ],
        "intermediateCodes": ["50233698", "50233699", "50233700", "50233701"],
        "dimensions": {
            "leftDecapeMm": 11.0,
            "rightDecapeMm": 6.0,
            "segmentLengthsMm": [232.0, 133.0, 133.0, 214.0],
            "cotaDecapeValuesMm": [11.0, 6.0, 7.0, 3.0],
            "decapeIndication": {"left": True, "right": True},
        },
    }


def test_90263954_catalog_alternate_codes_not_extra_when_primary_present():
    result = ChatDrawingBomComparisonService.compare(
        root=_payload_90263954(),
        pdf_extract=_pdf_extract_90263954(),
        product_code="90263954",
    )

    assert "10400111" not in result.extra_in_pdf
    assert "10400112" not in result.extra_in_pdf


def test_90263954_no_false_decape_right_mismatch_when_cotas_have_both_sides():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90263954(),
        pdf_extract=_pdf_extract_90263954(),
        product_code="90263954",
    )

    decape_errors = [
        item
        for item in items
        if "Decape direito" in str(item.get("item"))
        and item.get("status") == "error"
    ]

    assert not decape_errors


def test_90263954_pi_mi_quantity_not_pending_when_pdf_shows_one_per_chicote():
    pdf_extract = {
        **_pdf_extract_90263954(),
        "bomRows": [
            {"code": "50233698", "quantity": "1"},
            {"code": "50233699", "quantity": "1"},
            {"code": "50233700", "quantity": "1"},
            {"code": "50233701", "quantity": "1"},
        ],
    }

    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=_payload_90263954(),
        pdf_extract=pdf_extract,
        product_code="90263954",
    )
    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=_payload_90263954(),
        pdf_extract=pdf_extract,
        product_code="90263954",
    )

    assert not pending
    assert not mismatches
