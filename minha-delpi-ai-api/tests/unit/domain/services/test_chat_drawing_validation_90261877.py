"""Regressão — desenho 90261877 (PRE-DECAPE + grade revisão não viram decape E)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_dimensions_extraction_service import (
    ChatDrawingDimensionsExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90261877() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50222710",
                    "description": "CB22BRAN-00282/04/10-0600-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080106", "quantity": 1000.0},
                        {"code": "10380094", "quantity": 282.0},
                    ],
                },
                {
                    "code": "50222711",
                    "description": "CB22LARA-00282/04/10-0600-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080106", "quantity": 1000.0},
                        {"code": "10380097", "quantity": 282.0},
                    ],
                },
                {
                    "code": "50222712",
                    "description": "CB22AZUL-00262/04/10-0600-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080106", "quantity": 1000.0},
                        {"code": "10380096", "quantity": 262.0},
                    ],
                },
                {
                    "code": "50222713",
                    "description": "CB22AMAR-00262/04/10-0600-0000",
                    "quantity": 1.0,
                    "components": [
                        {"code": "10080106", "quantity": 1000.0},
                        {"code": "10380098", "quantity": 262.0},
                    ],
                },
            ]
        },
    }


def _cad_text_90261877() -> str:
    return """
    50222710
    CB22BRAN-00282/04/10-0600-0000
    10
    ±1
    262
    ±2
    10
    ±1
    282
    ±2
    10
    ±1
    282
    ±2
    10
    ±1
    262
    ±2
    RETIRAR O PRE-DECAPE
    1 | 2 | 3 | 4
    10 | ±1
    282 | ±2
    B | 10 | ±1 | G
    282 | ±2
    10 | ±1
    262 | ±2
    D | RETIRAR O PRE-DECAPE | I
    """


def test_90261877_pre_decape_and_revision_grid_do_not_set_left_decape():
    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(_cad_text_90261877())

    assert dims["leftDecapeMm"] is None
    assert dims["rightDecapeMm"] == 10.0
    assert dims["decapeIndication"] == {"left": False, "right": True}
    assert 262.0 in dims["segmentLengthsMm"]
    assert 282.0 in dims["segmentLengthsMm"]


def test_90261877_no_false_decape_mismatch_for_intermediates():
    pdf_extract = {
        "legible": True,
        "componentCodes": [
            "50222710",
            "50222711",
            "50222712",
            "50222713",
            "10080106",
            "10380094",
            "10380096",
            "10380097",
            "10380098",
        ],
        "intermediateCodes": ["50222710", "50222711", "50222712", "50222713"],
        "dimensions": ChatDrawingDimensionsExtractionService.extract_dimensions(
            _cad_text_90261877()
        ),
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90261877(),
        pdf_extract=pdf_extract,
        product_code="90261877",
    )

    decape_errors = [
        item
        for item in items
        if item.get("templateKey") == "decape_mismatch"
        and item.get("status") == "error"
    ]

    assert not decape_errors
