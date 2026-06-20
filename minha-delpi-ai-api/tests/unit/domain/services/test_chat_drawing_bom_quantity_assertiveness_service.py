from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_quantity_assertiveness_service import (
    ChatDrawingBomQuantityAssertivenessService,
)

configure_domain_infrastructure_ports()


def test_rejects_quantity_matching_description_dimension():
    row = {
        "code": "10090050",
        "quantity": "6.35",
        "description": "ISOLADOR NYLON RETO 6,35 NU UL94V-2",
    }
    reason = ChatDrawingBomQuantityAssertivenessService._untrusted_reason(
        row=row,
        code="10090050",
        quantity=6.35,
        api_row=None,
        root={},
        pdf_extract={},
    )

    assert reason in {"quantity_from_description", "decimal_piece_quantity"}


def test_column_quantity_source_skips_description_noise():
    row = {
        "code": "10090050",
        "quantity": "1",
        "description": "ISOLADOR NYLON RETO 6,35 NU UL94V-2",
        "quantitySource": "column",
        "quantityTrusted": True,
    }
    reason = ChatDrawingBomQuantityAssertivenessService._untrusted_reason(
        row=row,
        code="10090050",
        quantity=1.0,
        api_row=None,
        root={},
        pdf_extract={},
    )

    assert reason is None


def test_rejects_intermediate_length_as_quantity():
    row = {
        "code": "50212969",
        "quantity": "00120",
        "description": "/05/06-0000-0000 CABO PVC",
    }
    reason = ChatDrawingBomQuantityAssertivenessService._untrusted_reason(
        row=row,
        code="50212969",
        quantity=120.0,
        api_row=None,
        root={},
        pdf_extract={},
    )

    assert reason == "intermediate_length_as_quantity"
