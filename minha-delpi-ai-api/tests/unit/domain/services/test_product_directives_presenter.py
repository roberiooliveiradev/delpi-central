from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _sample_root() -> dict:
    return {
        "resolution": {
            "identifier": "90260882",
            "identifier_type": "delpi_code",
            "delpi_code": "90260882",
            "customer_reference": "10018137",
        },
        "product": {
            "product_code": "90260882",
            "description": "PROTETOR TERM CABO",
        },
        "structure": {
            "items": [
                {
                    "level": 1,
                    "parent_code": "90260882",
                    "parent_description": "PROTETOR TERM CABO",
                    "component_code": "50250258",
                    "component_description": "CONJUNTO TERMOSTATO",
                    "component_type": "PI",
                    "component_unit": "MI",
                    "quantity_per": "1",
                    "accumulated_quantity": "1",
                },
                {
                    "level": 2,
                    "parent_code": "50250258",
                    "parent_description": "CONJUNTO TERMOSTATO",
                    "component_code": "10080001",
                    "component_description": "MP TESTE",
                    "component_type": "MP",
                    "component_unit": "PC",
                    "quantity_per": "1000",
                    "accumulated_quantity": "1000",
                },
            ]
        },
        "summary": {
            "total_raw_material_entries": 1,
            "total_supplier_links": 2,
            "raw_materials_with_last_purchase": 1,
            "raw_materials_without_last_purchase": 0,
        },
        "raw_materials": [
            {
                "raw_material_code": "10080001",
                "description": "MP TESTE",
                "level": 2,
                "accumulated_quantity": "1000",
                "suppliers": [
                    {
                        "supplier_code": "000052",
                        "supplier_store": "01",
                        "supplier_name": "FORN A",
                        "supplier_part_number": "PN-001",
                        "last_price": 10.5,
                        "last_price_date": "20260101",
                    },
                    {
                        "supplier_code": "000089",
                        "supplier_store": "01",
                        "supplier_name": "FORN B",
                        "supplier_part_number": "PN-002",
                    },
                ],
                "last_purchase": {
                    "branch": "02",
                    "invoice_number": "123456",
                    "invoice_series": "1",
                    "issue_date": "20260115",
                    "entry_date": "20260116",
                    "supplier_code": "000052",
                    "supplier_name": "FORN A",
                    "supplier_part_number": "PN-001",
                    "quantity": 1000,
                    "unit_price": 10.5,
                    "total_value": 10500,
                    "icms_rate": 7.0,
                    "purchase_order": "039999",
                },
            }
        ],
    }


def test_entity_from_path_directives():
    assert (
        ChatOperationalResponseProfileService._entity_from_path(
            "/products/directives/90260882"
        )
        == "product_directives"
    )


def test_present_product_directives_builds_separate_tables():
    presenter = ExternalActionResultPresenter()
    root = _sample_root()
    path = "/products/directives/90260882"

    humanized = presenter._present_product_directives(root, path)

    assert "90260882" in humanized["titulo"]
    assert humanized["linhas"]
    assert len(humanized["tables"]) == 3
    assert humanized["tables"][0]["role"] == "structure"
    assert humanized["tables"][1]["role"] == "list"
    assert "FORN A" in str(humanized["tables"][1]["rows"][0].get("supplier_name"))

    table_presentations = presenter.build_product_directives_table_presentations(root, path)

    assert len(table_presentations) == 3
    assert table_presentations[0]["title"] == "Estrutura do produto (BOM)"
    assert len(table_presentations[0]["rows"]) == 1
    assert table_presentations[0]["rows"][0]["raw_material_code"] == "10080001"
    structure_cols = [column["key"] for column in table_presentations[0]["columns"]]
    assert structure_cols[:2] == ["raw_material_code", "description"]
    assert table_presentations[1]["title"] == "Fornecedores por matéria-prima"
    assert len(table_presentations[1]["rows"]) == 2
    supplier_cols = [column["key"] for column in table_presentations[1]["columns"]]
    assert supplier_cols[:2] == ["raw_material_code", "raw_material_description"]
    assert table_presentations[2]["title"] == "Última compra por matéria-prima"
    assert table_presentations[2]["rows"][0]["invoice_number"] == "123456"
    last_cols = [column["key"] for column in table_presentations[2]["columns"]]
    assert last_cols[:2] == ["raw_material_code", "description"]
