from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_product_unit_conversion_service import (
    ChatDrawingProductUnitConversionService,
)

configure_domain_infrastructure_ports()


def test_apply_conversion_factor_multiply():
    assert (
        ChatDrawingProductUnitConversionService.apply_conversion_factor(2.0, 1000.0, "M")
        == 2000.0
    )


def test_apply_conversion_factor_divide():
    assert (
        ChatDrawingProductUnitConversionService.apply_conversion_factor(2000.0, 1000.0, "D")
        == 2.0
    )


def test_quantity_to_mm_physical_mt():
    assert ChatDrawingProductUnitConversionService.quantity_to_mm(0.65, "MT") == 650.0


def test_quantity_to_mm_via_component_secondary_mm():
    item = {
        "code": "10130009",
        "unit": "CX",
        "secondary_unit": "MM",
        "conversion_factor": 650.0,
        "conversion_type": "M",
        "quantity": 1.0,
    }

    assert (
        ChatDrawingProductUnitConversionService.quantity_to_mm_from_structure_item(1.0, item)
        == 650.0
    )


def test_per_piece_mm_with_mi_batch_scale():
    item = {
        "code": "10120073",
        "unit": "MT",
        "quantity": 650.0,
    }

    assert (
        ChatDrawingProductUnitConversionService.per_piece_mm(
            quantity=650.0,
            unit="MT",
            batch_scale=1000.0,
            item=item,
        )
        == 650.0
    )


def test_quantity_to_mm_via_third_unit_chain():
    item = {
        "code": "10139999",
        "unit": "CX",
        "secondary_unit": "UN",
        "conversion_factor": 1.0,
        "conversion_type": "M",
        "third_unit": "MM",
        "third_conversion_factor": 650.0,
        "quantity": 1.0,
    }

    assert (
        ChatDrawingProductUnitConversionService.quantity_to_mm_from_structure_item(1.0, item)
        == 650.0
    )
