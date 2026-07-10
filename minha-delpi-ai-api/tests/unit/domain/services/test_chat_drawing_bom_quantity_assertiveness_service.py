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


def test_rejects_quantity_matching_dimension_from_stamp_line_when_row_truncated():
    row = {
        "code": "10120073",
        "quantity": "12.",
        "description": "00X0,80 PT 130°C 1,5KV PVC ROHS",
    }
    pdf_extract = {
        "sourceMetadata": {
            "stampText": "B | 1 | 10120073 [TUBO ISOLANTE 12,00X0,80 PT 130°C 1,5KV PVC ROHS",
        }
    }
    reason = ChatDrawingBomQuantityAssertivenessService._untrusted_reason(
        row=row,
        code="10120073",
        quantity=12.0,
        api_row=None,
        root={},
        pdf_extract=pdf_extract,
    )

    assert reason == "quantity_from_description"


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


def test_mismatch_status_requires_trusted_quantity_source_for_critical():
    pdf_extract = {
        "bomRows": [
            {
                "code": "10090050",
                "quantity": "6.35",
                "quantitySource": "line_heuristic",
                "quantityTrusted": True,
            }
        ]
    }
    status = ChatDrawingBomQuantityAssertivenessService.mismatch_status(
        trusted=True,
        pdf_extract=pdf_extract,
        code="10090050",
    )

    assert status == "pending"


def test_column_inferred_quantity_source_skips_description_noise():
    row = {
        "code": "10090050",
        "quantity": "1",
        "description": "ISOLADOR NYLON RETO 6,35 NU UL94V-2",
        "quantitySource": "column_inferred",
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


def test_refined_column_without_row_description_uses_api_description_noise():
    row = {
        "code": "10091137",
        "quantity": "4",
        "description": None,
        "quantitySource": "refined_column",
        "quantityTrusted": True,
    }
    root = _payload_like_root()
    root["structure"] = {
        "items": [
            {
                "code": "10091137",
                "description": "CONECTOR RETO 4 VIAS NU UL 94V-0",
                "type": "MP",
                "unit": "PC",
                "quantity": 1000.0,
                "components": [],
            }
        ]
    }
    reason = ChatDrawingBomQuantityAssertivenessService._untrusted_reason(
        row=row,
        code="10091137",
        quantity=4.0,
        api_row=None,
        root=root,
        pdf_extract={},
    )

    assert reason == "quantity_from_description"


def _payload_like_root() -> dict:
    return {
        "product": {
            "code": "90263655",
            "unit": "MI",
            "pa_reference": {"catalog_unit": "MI", "catalog_pieces_per_unit": 1000.0},
        }
    }


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
