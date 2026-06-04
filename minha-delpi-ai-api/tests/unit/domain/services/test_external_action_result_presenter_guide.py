from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_analyser_guide_items_humanized_not_raw_dict():
    presenter = ExternalActionResultPresenter()
    root = {
        "product": {"code": "90260015", "description": "CHICOTE"},
        "guide": {
            "items": [
                {
                    "product_code": "90260015",
                    "bom_level": 0,
                    "operations": [
                        {
                            "operation_code": "01",
                            "operation_description": "EMBALAR",
                            "work_center": "CT-19",
                        }
                    ],
                },
                {
                    "product_code": "50210372",
                    "bom_level": 1,
                    "operations": [
                        {
                            "operation_code": "01",
                            "operation_description": "CORTAR / DECAPAR - MAQUINA",
                            "work_center": "CT-01A",
                        }
                    ],
                },
            ]
        },
    }

    result = presenter._present_product_analyser(root, root["product"], "/products/90260015/analyser")
    body = "\n".join(result.get("linhas") or [])

    assert "Operations=" not in body

    tables = presenter.build_analyser_auxiliary_table_presentations(root)
    guide_table = next(
        table
        for table in tables
        if "roteiro" in str(table.get("title") or "").lower()
    )
    serialized_rows = " ".join(str(row) for row in guide_table.get("rows") or [])

    assert "EMBALAR" in serialized_rows
    assert "90260015" in serialized_rows
    assert "CORTAR" in serialized_rows
