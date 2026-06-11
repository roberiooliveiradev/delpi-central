from tests.fixtures.presentation_render_plan_gate import (
    P6_EXTENDED_PIPELINE_CASES,
    validate_render_plan_for_ci,
)


def test_tier_a_pipeline_cases_emit_render_plan_contract():
    result = validate_render_plan_for_ci()

    assert result["ok"], result.get("renderPlanGaps")


def test_p6_extended_pipeline_cases_are_included_in_gate():
    result = validate_render_plan_for_ci()
    gaps = {gap.get("case_id") for gap in result.get("renderPlanGaps") or []}

    for case in P6_EXTENDED_PIPELINE_CASES:
        assert case["id"] not in gaps, f"gap em caso estendido {case['id']}: {gaps}"
