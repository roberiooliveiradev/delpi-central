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
