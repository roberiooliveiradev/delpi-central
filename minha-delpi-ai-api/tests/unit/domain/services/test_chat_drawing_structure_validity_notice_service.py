from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_bom_quantity_semantics_service import (
    ChatDrawingBomQuantitySemanticsService,
)
from app.domain.services.chat_drawing_structure_validity_notice_service import (
    ChatDrawingStructureValidityNoticeService,
)

configure_domain_infrastructure_ports()


def test_structure_validity_ok_when_current_filter():
    items = ChatDrawingStructureValidityNoticeService.build_check_items(
        product={"current_revision": "08"},
        pdf_extract={"internalRevision": "08"},
        structure={"bom_validity": {"filter": "current", "validityColumns": "G1_INI,G1_FIM"}},
    )

    assert any(item.get("templateKey") == "structure_bom_validity_ok" for item in items)


def test_structure_validity_pending_when_pdf_revision_lags():
    items = ChatDrawingStructureValidityNoticeService.build_check_items(
        product={"current_revision": "08"},
        pdf_extract={"internalRevision": "04"},
        structure={"bom_validity": {"filter": "current", "validityColumns": "G1_INI,G1_FIM"}},
    )

    assert any(
        item.get("templateKey") == "structure_bom_validity_revision_lag"
        and item.get("status") == "pending"
        for item in items
    )


def test_length_consumable_tubo_prefix():
    assert ChatDrawingBomQuantitySemanticsService.is_length_consumable_material(
        "10120073",
        "TUBO ISOLANTE",
    )


def test_length_consumable_termo_marker():
    assert ChatDrawingBomQuantitySemanticsService.is_length_consumable_material(
        "10500020",
        "TERMOENCOLHIVEL 3,20X0,40",
    )


def test_length_consumable_normalizes_with_segment_mm():
    root = {
        "product": {"code": "90262008", "unit": "MI"},
        "structure": {
            "items": [
                {
                    "code": "10120073",
                    "quantity": 650.0,
                    "unit": "MT",
                    "description": "TUBO ISOLANTE",
                }
            ]
        },
    }
    pdf_extract = {"dimensions": {"segmentLengthsMm": [650.0]}}

    result = ChatDrawingBomQuantitySemanticsService.normalize_pdf_quantity(
        pdf_quantity=1.0,
        api_row=ChatDrawingBomQuantitySemanticsService.collect_structure_quantities(
            root,
            "90262008",
        )["10120073"],
        root=root,
        pdf_extract=pdf_extract,
    )

    assert result.comparable is True
    assert result.pdf_value == 650.0
