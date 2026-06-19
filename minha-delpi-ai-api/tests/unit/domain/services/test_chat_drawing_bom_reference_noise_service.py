from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_total_length_reference_service import (
    ChatDrawingTotalLengthReferenceService,
)

configure_domain_infrastructure_ports()


def test_client_reference_row_detected_from_dc_z_pattern():
    row = {
        "code": "10056570",
        "quantity": "855",
        "description": "REV: 15",
    }

    assert ChatDrawingBomReferenceNoiseService.is_client_reference_row(row)


def test_collect_reference_noise_codes_from_pdf_extract():
    pdf_extract = {
        "bomRows": [
            {
                "code": "10056570",
                "quantity": "855",
                "description": "REV: 15",
            }
        ],
        "sourceMetadata": {
            "stampText": "10056570 DC:Z-855 REV: 15",
        },
    }

    codes = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(pdf_extract)

    assert "10056570" in codes


def test_client_reference_block_ref_z_weg_pattern():
    text = """
REF:
Z-0555 REV:73
WEG INDUSTRIAS S.A.-MOTORES
10056551
90261656
"""
    pdf_extract = {
        "productCode": "90261656",
        "fullText": text,
        "componentCodes": ["10056551", "10080110", "10420256"],
    }

    codes = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(pdf_extract)

    assert "10056551" in codes
    assert "10080110" not in codes
    assert "10420256" not in codes


def test_total_length_uses_cable_child_not_pi_piece_count():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50222551",
                    "description": "CA0,75VDAR-00136/06/06-9800-2100",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10020194", "quantity": 136.0, "unit": "MT"},
                    ],
                }
            ]
        }
    }

    reference = ChatDrawingTotalLengthReferenceService.resolve(root)

    assert reference is not None
    assert reference.length_mm == 136.0
    assert reference.unit_label == "MT"


def test_total_length_uses_pi_quantity_with_length_unit():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50212194",
                    "description": "CB20PRET",
                    "quantity": 2.0,
                    "unit": "MI",
                    "components": [],
                }
            ]
        }
    }

    reference = ChatDrawingTotalLengthReferenceService.resolve(root)

    assert reference is not None
    assert reference.length_mm == 2.0
    assert reference.unit_label == "MI"
