"""Slide intelligence: JoinPlan / FormatHint / PresentationRecipe."""

from __future__ import annotations

import pytest

from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.services.data.display_format_hints_service import (
    DisplayFormatHintsService,
)
from tv_app.application.services.data.join_plan_service import JoinPlanService
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
    clear_presentation_recipes_cache,
)
from tv_app.application.services.data.tv_data_builder_draft import propose_join
from tv_app.domain.presentation_intelligence.models import (
    FormatHint,
    JoinPlanProposal,
    PresentationRecipeId,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()
    clear_presentation_recipes_cache()


def test_dto_fixtures_round_trip():
    join = JoinPlanProposal(left_key="branch", right_key="filial", confidence=0.9)
    assert join.is_usable
    assert join.to_dict()["mergeStep"]["op"] == "merge"

    fmt = FormatHint(
        category="currency",
        value_format="currency",
        currency="BRL",
        decimal_places=2,
    )
    assert fmt.kpi_options_patch()["valueFormat"] == "currency"
    assert fmt.display_format_spec()["currency"] == "BRL"

    recipe = PresentationRecipeId(recipe_id="TV_KPI_HERO", theme_key="delpi")
    assert recipe.to_dict()["recipeId"] == "TV_KPI_HERO"


def test_join_plan_positive_preferred_key():
    proposal = JoinPlanService.propose(
        left_columns=["branch", "value"],
        right_columns=["branch", "name"],
    )
    assert proposal is not None
    assert proposal.is_usable
    assert proposal.left_key == "branch"
    assert proposal.right_key == "branch"
    assert proposal.confidence >= 0.85


def test_join_plan_sibling_codigo():
    proposal = JoinPlanService.propose(
        left_columns=["Codigo", "qty"],
        right_columns=["codigo", "label"],
    )
    assert proposal is not None
    assert proposal.left_key.lower() == "codigo"
    assert proposal.right_key.lower() == "codigo"


def test_join_plan_negative_no_common():
    proposal = JoinPlanService.propose(
        left_columns=["alpha", "beta"],
        right_columns=["gamma", "delta"],
    )
    assert proposal is None


def test_propose_join_uses_join_plan_not_default_op():
    draft = {
        "sources": [
            {"localId": "a", "label": "A", "columns": ["branch", "v"]},
            {"localId": "b", "label": "B", "columns": ["branch", "n"]},
        ],
        "primaryLocalId": "a",
    }
    next_draft, step = propose_join(draft)
    assert step is not None
    assert step["leftKey"] == "branch"
    assert step["rightKey"] == "branch"
    assert step["sourceId"] == "b"


def test_propose_join_negative_without_schema_does_not_invent_op():
    draft = {
        "sources": [
            {"localId": "a", "label": "A"},
            {"localId": "b", "label": "B"},
        ],
        "primaryLocalId": "a",
    }
    _, step = propose_join(draft)
    assert step is None


def test_format_hint_nl_and_field_and_type():
    assert DisplayFormatHintsService.from_nl("mostre em R$").value_format == "currency"
    assert DisplayFormatHintsService.from_nl("como percentual").value_format == "percent"
    assert DisplayFormatHintsService.from_field_key("late_percentage").value_format == "percent"
    assert (
        DisplayFormatHintsService.from_value_field_type("currency").currency == "BRL"
    )


def test_format_validation_rejects_garbage():
    errors = DisplayFormatHintsService.validate_projection_formats(
        {"kpiOptions": {"valueFormat": "banana"}}
    )
    assert "kpiOptions.valueFormat" in errors
    assert DisplayFormatHintsService.validate_projection_formats(
        {"kpiOptions": {"valueFormat": "percent"}}
    ) == []


def test_presentation_recipes_resolve_and_ops():
    rid = PresentationRecipeService.resolve_from_nl("quero um kpi hero na TV")
    assert rid is not None
    assert rid.recipe_id == "TV_KPI_HERO"
    ops = PresentationRecipeService.ops_for_recipe("TV_KPI_HERO")
    assert any(op.get("op") == "patch_native_config" for op in ops)
    theme = PresentationRecipeService.resolve_from_nl("deixe mais profissional")
    assert theme is not None
    assert theme.recipe_id == "THEME_MIDNIGHT"


def test_agent_directives_project_slide_intelligence():
    directives = VistaAgentIntelligenceService.agent_directives()
    assert directives["compound_slide"]["principle"] == "READY_COMPOUND_SLIDE"
    assert directives["display_format"]["principle"] == "TYPED_DISPLAY_FORMAT"
    assert directives["media_limits"]["principle"] == "ASSET_ID_ONLY"
    assert "COMPOUND_READY_SLIDE" in directives["modes"]
    catalog = directives["presentation_recipes"]["catalog"]
    assert "TV_KPI_HERO" in catalog["recipes"]
    assert "Inter, system-ui, sans-serif" in catalog["fontFamilyAllowlist"]
    assert "delpi_navy" in catalog["colorRamps"]


def test_format_validation_rejects_garbage_and_message():
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
        clear_presentation_ops_content_cache,
    )

    errors = DisplayFormatHintsService.validate_projection_formats(
        {"kpiOptions": {"valueFormat": "banana"}}
    )
    assert "kpiOptions.valueFormat" in errors
    assert DisplayFormatHintsService.validate_projection_formats(
        {"kpiOptions": {"valueFormat": "percent"}}
    ) == []

    clear_presentation_ops_content_cache()
    msg = PresentationOpsContentService.message(
        "displayFormatInvalid", field="kpiOptions.valueFormat"
    )
    assert "kpiOptions.valueFormat" in msg


def test_suggest_theme_recipe_mais_profissional():
    from tv_app.application.services.data.presentation_suggest_ops_service import (
        PresentationSuggestOpsService,
    )

    result = PresentationSuggestOpsService.suggest(
        message="deixe mais profissional",
        host_context={"playlistId": "p1", "slideId": "s1"},
    )
    ops = result.get("ops") or []
    assert ops
    assert any(op.get("op") == "patch_native_config" for op in ops)


def test_join_candidate_keys_from_columns():
    keys = JoinPlanService.candidate_keys_from_columns(
        ["alpha", "branch", "value", "id"]
    )
    assert keys[0] == "branch"
    assert "id" in keys
