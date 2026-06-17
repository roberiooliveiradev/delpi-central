from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
    ROW_EMPHASIS_EXCLUSIVE_MP,
    enrich_structure_rows,
)


def test_enrich_structure_rows_marks_exclusive_mp_with_row_emphasis():
    rows = enrich_structure_rows(
        [
            {
                "component_type": "MP",
                "product_code": "10019001",
                "exclusive_raw_material": "SIM",
            },
            {
                "component_type": "MP",
                "product_code": "10019002",
                "exclusive_raw_material": "NAO",
            },
        ]
    )

    assert rows[0]["row_emphasis"] == ROW_EMPHASIS_EXCLUSIVE_MP
    assert rows[0]["exclusive_raw_material_label"] == "Sim"
    assert "row_emphasis" not in rows[1]
