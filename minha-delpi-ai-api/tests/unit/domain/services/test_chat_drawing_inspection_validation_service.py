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
