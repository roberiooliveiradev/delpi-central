from app.domain.services.chat_drawing_inspection_validation_service import (
    ChatDrawingInspectionValidationService,
)


def test_has_inspection_plan_legacy_qp_keys():
    assert ChatDrawingInspectionValidationService.has_inspection_plan(
        {"items": [{"QP6": [{"QP6_PRODUT": "90260140"}]}]}
    )


def test_has_inspection_plan_measurable_tests():
    assert ChatDrawingInspectionValidationService.has_inspection_plan(
        {"items": [{"measurable_tests": [{"test_code": "506"}]}]}
    )


def test_has_inspection_plan_textual_tests():
    assert ChatDrawingInspectionValidationService.has_inspection_plan(
        {"items": [{"textual_tests": [{"test_code": "504", "text": "ok"}]}]}
    )


def test_has_inspection_plan_empty_items():
    assert not ChatDrawingInspectionValidationService.has_inspection_plan({"items": []})


def test_has_inspection_plan_items_without_tests():
    assert not ChatDrawingInspectionValidationService.has_inspection_plan(
        {"items": [{"product": "90262834", "level": 0}]}
    )


def test_row_plan_counts_measurable_textual_contract():
    row = {
        "product_code": "90261647",
        "bom_level": 0,
        "header": {"product_code": "90261647", "revision": "02"},
        "measurable_tests": [{"test_code": "01"}, {"test_code": "02"}],
        "textual_tests": [{"test_code": "504"}],
    }

    assert ChatDrawingInspectionValidationService.row_plan_counts(row) == (1, 2, 1)
    assert ChatDrawingInspectionValidationService.row_level(row) == 0
    assert ChatDrawingInspectionValidationService.row_product_code(row) == "90261647"


def test_row_plan_counts_legacy_qp_keys():
    row = {
        "product": "90260140",
        "level": 0,
        "QP6": [{"QP6_PRODUT": "90260140"}],
        "QP7": [{"QP7_ENSAIO": "506"}, {"QP7_ENSAIO": "507"}],
        "QP8": [{"QP8_ENSAIO": "504"}],
    }

    assert ChatDrawingInspectionValidationService.row_plan_counts(row) == (1, 2, 1)


def test_flatten_measurable_and_textual_rows_from_api_contract():
    row = {
        "product_code": "90261647",
        "bom_level": 0,
        "header": {
            "revision": "02",
            "description": "CHICOTE DE ATERRAMENTO",
        },
        "measurable_tests": [
            {
                "operation": "01",
                "test_code": "01",
                "labor": "LABFIS",
                "nominal_value": "290",
                "lower_spec_limit": "285",
                "upper_spec_limit": "295",
                "unit": "MM",
            }
        ],
        "textual_tests": [
            {
                "operation": "01",
                "test_code": "12",
                "text": "10420256",
            }
        ],
    }

    measurable = ChatDrawingInspectionValidationService.flatten_measurable_rows(row)
    textual = ChatDrawingInspectionValidationService.flatten_textual_rows(row)
    export_rows = ChatDrawingInspectionValidationService.flatten_export_rows(row)

    assert measurable == [
        {
            "operation": "01",
            "test": "01",
            "lab": "LABFIS",
            "nominal": "290",
            "lower": "285",
            "upper": "295",
            "unit": "MM",
        }
    ]
    assert textual == [{"operation": "01", "test": "12", "text": "10420256"}]
    assert len(export_rows) == 2
    assert export_rows[0]["section"] == "Dimensional"
    assert export_rows[1]["detail"] == "10420256"
