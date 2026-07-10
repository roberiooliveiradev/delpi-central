from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_reference_noise_service import (
    ChatDrawingBomReferenceNoiseService,
)
from app.domain.services.chat_drawing_total_length_reference_service import (
    ChatDrawingTotalLengthReferenceService,
)

configure_domain_infrastructure_ports()


def test_wire_gauge_row_detected_as_reference_noise():
    row = {
        "code": "10061667",
        "quantity": "2",
        "description": "20ANG OURO ROHS (FLEXTRONIGS)",
        "quantitySource": "refined_column",
        "quantityTrusted": True,
    }

    assert ChatDrawingBomReferenceNoiseService.is_client_reference_row(row)


def test_collect_reference_noise_codes_filters_wire_gauge_false_code():
    pdf_extract = {
        "productCode": "90264227",
        "bomRows": [
            {
                "code": "10061667",
                "quantity": "2",
                "description": "20ANG OURO ROHS (FLEXTRONIGS)",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            },
            {
                "code": "50215425",
                "quantity": "36",
                "description": "CT26VERM-00036/04/06-0000-0000",
            },
        ],
        "componentCodes": ["10061667", "50215425"],
    }

    codes = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(pdf_extract)

    assert "10061667" in codes
    assert "50215425" not in codes


def test_collect_reference_noise_codes_filters_wire_gauge_inline_from_bom_haystack():
    pdf_extract = {
        "productCode": "90264227",
        "componentCodes": ["10061667", "50215425"],
        "sourceMetadata": {
            "regionTexts": {
                "bom": (
                    "[6 | 2 | 10061667 [TERN PIGO-LOGK 22-20ANG OURO ROHS (FLEXTRONIGS)\n"
                    "1 50215425 CT26VERM-00036/04/06-0000-0000"
                )
            }
        },
    }

    codes = ChatDrawingBomReferenceNoiseService.collect_reference_noise_codes(pdf_extract)

    assert "10061667" in codes
    assert "50215425" not in codes


def test_valid_cable_row_with_awg_in_description_is_not_noise():
    row = {
        "code": "10020033",
        "quantity": "1",
        "description": "CABO PVC 105°C 22AWG VM 600V NBR 9117",
    }

    assert not ChatDrawingBomReferenceNoiseService.is_client_reference_row(row)


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
    assert reference.unit_label == "mm"


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


def test_false_intermediate_bom_row_termoencolhivel_noise():
    row = {
        "code": "50250279",
        "description": "LUVATERMOENCOLHVEL =",
        "quantitySource": "column",
    }

    assert ChatDrawingBomReferenceNoiseService.is_false_intermediate_bom_row(row)
    assert ChatDrawingBomReferenceNoiseService.is_client_reference_row(row)


def test_intermediate_bom_row_with_date_path_is_not_false():
    row = {
        "code": "50222736",
        "description": "/10/04-0000-0600",
    }

    assert not ChatDrawingBomReferenceNoiseService.is_false_intermediate_bom_row(row)
