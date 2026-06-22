from app.application.services.bom_tree_builder import BomTreeBuilder


def test_bom_tree_builder_exposes_component_unit_conversion_fields() -> None:
    rows = [
        {
            "parent_code": "90262008",
            "parent_description": "CHICOTE",
            "parent_type": "PA",
            "parent_unit": "MI",
            "component_code": "10120073",
            "component_description": "TUBO ISOLANTE",
            "component_type": "MP",
            "component_unit": "MT",
            "component_secondary_unit": "MM",
            "component_conversion_factor": 1000.0,
            "component_conversion_type": "M",
            "quantity": 650.0,
            "bom_level": 1,
        }
    ]

    root = BomTreeBuilder.build(rows, "90262008")
    component = root.components[0].to_dict()

    assert component["code"] == "10120073"
    assert component["unit"] == "MT"
    assert component["secondary_unit"] == "MM"
    assert component["conversion_factor"] == 1000.0
    assert component["conversion_type"] == "M"


def test_bom_tree_builder_exposes_component_third_unit_conversion() -> None:
    rows = [
        {
            "parent_code": "90000001",
            "parent_description": "PA",
            "parent_type": "PA",
            "parent_unit": "UN",
            "component_code": "10139999",
            "component_description": "MP CX/MM/MT",
            "component_type": "MP",
            "component_unit": "CX",
            "component_secondary_unit": "MM",
            "component_conversion_factor": 1000.0,
            "component_conversion_type": "M",
            "component_third_unit": "MT",
            "component_third_conversion_factor": 1000.0,
            "quantity": 1.0,
            "bom_level": 1,
        }
    ]

    root = BomTreeBuilder.build(rows, "90000001")
    component = root.components[0].to_dict()

    assert component["third_unit"] == "MT"
    assert component["third_conversion_factor"] == 1000.0
