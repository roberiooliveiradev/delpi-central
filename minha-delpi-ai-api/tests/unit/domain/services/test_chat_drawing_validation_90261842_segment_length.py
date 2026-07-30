"""Âncora 90261842 — comprimento na descrição 50xx dispensa cota de trecho no PDF."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)

configure_domain_infrastructure_ports()

_PRODUCT = "90261842"


def _root_with_described_intermediates() -> dict:
    return {
        "product": {
            "code": _PRODUCT,
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "unit": "MI",
        },
        "structure": {
            "items": [
                {
                    "code": "50231200",
                    "description": "CA0,75AZUL-00185/14/06-0000-1145",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1,
                    "components": [
                        {
                            "code": "10020042",
                            "description": "CABO PVC",
                            "quantity": 185.0,
                            "unit": "MT",
                            "components": [],
                        }
                    ],
                },
                {
                    "code": "50231204",
                    "description": "CA0,75MARR-00285/14/06-0000-1145",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 1,
                    "components": [
                        {
                            "code": "10020048",
                            "description": "CABO PVC",
                            "quantity": 285.0,
                            "unit": "MT",
                            "components": [],
                        }
                    ],
                },
            ]
        },
    }


def test_segment_length_not_pending_when_50xx_description_declares_length():
    """OCR de cotas ruidosas (214, 65, 2…) não gera pendente se a descrição 50xx já tem comprimento."""
    pdf_extract = {
        "legible": True,
        "dimensions": {
            "segmentLengthsMm": [214.0, 2.0, 2.0, 65.0, 2.0],
        },
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=_root_with_described_intermediates(),
        pdf_extract=pdf_extract,
        product_code=_PRODUCT,
    )
    pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert not pending


def test_segment_length_pending_when_50xx_lacks_description_length():
    root = {
        "product": {"code": _PRODUCT, "description": "CHICOTE", "type": "PA", "unit": "MI"},
        "structure": {
            "items": [
                {
                    "code": "50231200",
                    "description": "INTERMEDIARIO SEM COMPRIMENTO NA DESCRICAO",
                    "type": "PI",
                    "components": [
                        {
                            "code": "10020042",
                            "quantity": 185.0,
                            "unit": "MT",
                            "components": [],
                        }
                    ],
                }
            ]
        },
    }
    pdf_extract = {
        "legible": True,
        "dimensions": {"segmentLengthsMm": [214.0, 65.0]},
    }

    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract=pdf_extract,
        product_code=_PRODUCT,
    )
    pending = [
        item
        for item in items
        if item.get("templateKey") == "segment_length_pending"
    ]

    assert pending
