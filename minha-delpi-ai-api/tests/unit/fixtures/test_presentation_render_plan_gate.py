from tests.fixtures.presentation_render_plan_gate import validate_render_plan_for_ci


def test_tier_a_pipeline_cases_emit_render_plan_contract():
    result = validate_render_plan_for_ci()

    assert result["ok"], result.get("renderPlanGaps")
