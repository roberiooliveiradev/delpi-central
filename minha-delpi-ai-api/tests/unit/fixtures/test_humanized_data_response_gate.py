from tests.fixtures.humanized_data_response_cases import HUMANIZED_DATA_SHAPE_CASES
from tests.fixtures.humanized_data_response_gate import (
    validate_humanized_answer_for_ci,
    validate_humanized_shape_cases,
)


def test_humanized_shape_cases_cover_playbook_shapes():
    shapes = {str(case["shape"]) for case in HUMANIZED_DATA_SHAPE_CASES}

    assert "field_value_profile" in shapes
    assert "generic_list" in shapes
    assert "logical_error" in shapes
    assert len(HUMANIZED_DATA_SHAPE_CASES) >= 10


def test_validate_humanized_shape_cases_passes():
    assert validate_humanized_shape_cases() == []


def test_validate_humanized_answer_for_ci_passes():
    validation = validate_humanized_answer_for_ci()

    assert validation["ok"] is True
    assert validation["gapCount"] == 0
