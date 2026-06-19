"""Regressão — desenho 90264206 (decape E/D por lado, nota de máquina 4 mm)."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_dimensions_extraction_service import (
    ChatDrawingDimensionsExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()


def _payload_90264206() -> dict:
    return {
        "structure": {
            "items": [
                {
                    "code": "50215423",
                    "description": "CT26VERM-00036/04/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440133", "quantity": 36.0}],
                },
                {
                    "code": "50215424",
                    "description": "CT26PRET-000062/04/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440134", "quantity": 62.0}],
                },
                {
                    "code": "50215431",
                    "description": "CT26PRET-00050/2,5/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440134", "quantity": 50.0}],
                },
                {
                    "code": "50215432",
                    "description": "CT26VERM-00040/2,5/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440133", "quantity": 40.0}],
                },
            ]
        },
    }


def _pdf_extract_90264206() -> dict:
    return {
        "legible": True,
        "componentCodes": ["50215423", "50215424", "50215431", "50215432"],
        "intermediateCodes": ["50215423", "50215424", "50215431", "50215432"],
        "dimensions": {
            "leftDecapeMm": 4.0,
            "rightDecapeMm": 6.0,
            "totalLengthMm": 162.0,
            "segmentLengthsMm": [140.0, 150.0, 136.0, 162.0],
            "cotaDecapeValuesMm": [6.0],
        },
    }


def test_90264206_extract_machine_side_decape_overrides_global_note():
    text = """
    ENROLAR AS DUAS PONTAS COM DECAPE DE 6MM,
    DECAPAR O LADO DE 4MM NA MÁQUINA
    6±140±1
    6±150±1
    """

    dims = ChatDrawingDimensionsExtractionService.extract_dimensions(text)

    assert dims["leftDecapeMm"] == 4.0
    assert dims["rightDecapeMm"] == 6.0
    assert dims["cotaDecapeValuesMm"] == [6.0]


def test_90264206_no_false_decape_mismatch_for_04_06_intermediates():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264206(),
        pdf_extract=_pdf_extract_90264206(),
        product_code="90264206",
    )

    decape_errors = [
        item
        for item in items
        if item.get("item", "").startswith("Decape")
        and item.get("status") == "error"
    ]

    assert not any("50215423" in str(item.get("item")) for item in decape_errors)
    assert not any("50215424" in str(item.get("item")) for item in decape_errors)


def test_90264206_decape_validation_uses_correct_side_not_global_left_for_right():
    items = ChatDrawingStructureValidationService.build_check_items(
        root=_payload_90264206(),
        pdf_extract=_pdf_extract_90264206(),
        product_code="90264206",
    )

    assert not any(
        "Decape direito" in str(item.get("item")) and item.get("status") == "error"
        for item in items
    )
