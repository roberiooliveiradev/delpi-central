from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_bom_quantity_validation_service import (
    ChatDrawingBomQuantityValidationService,
)
from app.domain.services.chat_drawing_total_length_reference_service import (
    ChatDrawingTotalLengthReferenceService,
)

configure_domain_infrastructure_ports()


def _root_90264238() -> dict:
    return {
        "product": {
            "code": "90264238",
            "type": "PA",
            "unit": "MI",
            "quantity": 1.0,
        },
        "structure": {
            "items": [
                {
                    "code": "10080308",
                    "quantity": 2000.0,
                    "unit": "PC",
                    "description": "TERM. OLHAL M6",
                    "components": [],
                },
                {
                    "code": "10130009",
                    "quantity": 50.0,
                    "unit": "MT",
                    "description": "TERMOENCOLHIVEL",
                    "components": [],
                },
                {
                    "code": "10400173",
                    "quantity": 810.0,
                    "unit": "MT",
                    "description": "CABO SIL 200°C 6,00MM2",
                    "components": [],
                },
            ]
        },
    }


def test_milheiro_scales_pc_quantity_from_pdf_per_piece():
    root = _root_90264238()
    pdf_extract = {
        "bomRows": [{"code": "10080308", "quantity": "2"}],
    }

    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264238",
    )

    assert not mismatches


def test_cable_mt_quantity_uses_drawing_length_and_milheiro_scale():
    root = _root_90264238()
    pdf_extract = {
        "bomRows": [{"code": "10400173", "quantity": "1"}],
        "dimensions": {"totalLengthMm": 810.0},
    }

    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264238",
    )

    assert not mismatches


def test_total_length_reference_uses_cable_mt_per_piece_for_pa_mi():
    reference = ChatDrawingTotalLengthReferenceService.resolve(_root_90264238())

    assert reference is not None
    assert reference.length_mm == 810.0
    assert reference.unit_label == "mm"


def test_termoencolhivel_mt_without_drawing_length_is_pending_not_mismatch():
    root = _root_90264238()
    pdf_extract = {
        "bomRows": [{"code": "10130009", "quantity": "2"}],
    }

    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264238",
    )
    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264238",
    )

    assert not mismatches
    assert any(row.code == "10130009" for row in pending)


def test_batch_scale_for_mi_root():
    assert ChatDrawingBomQuantitySemanticsService.batch_scale_for_root(_root_90264238()) == 1000.0


def test_intermediate_pi_mi_quantity_compares_one_to_one():
    root = {
        "product": {"code": "90263954", "unit": "MI"},
        "structure": {
            "items": [
                {
                    "code": "50233698",
                    "quantity": 1.0,
                    "unit": "MI",
                    "type": "PI",
                    "components": [],
                }
            ]
        },
    }
    pdf_extract = {
        "bomRows": [{"code": "50233698", "quantity": "1"}],
    }

    pending = ChatDrawingBomQuantityValidationService.collect_pending(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263954",
    )
    mismatches = ChatDrawingBomQuantityValidationService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263954",
    )

    assert not pending
    assert not mismatches
