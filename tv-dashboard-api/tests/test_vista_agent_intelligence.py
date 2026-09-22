"""Deployable VISTA agent_directives (object resolution + anti-duplicidade)."""

from __future__ import annotations

from tv_app.application.gpt_actions.capability_surface import build_capability_surface
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)


def setup_function() -> None:
    clear_vista_agent_intelligence_cache()


def teardown_function() -> None:
    clear_vista_agent_intelligence_cache()


def test_agent_directives_prefer_alter_existing_before_create():
    directives = VistaAgentIntelligenceService.agent_directives()
    resolution = directives["object_resolution"]
    assert resolution["principle"] == "ALTER_EXISTING_BEFORE_CREATE"
    rules = " ".join(resolution["rules"])
    assert "NÃO create_playlist" in rules or "create_playlist" in rules
    assert "patch_native_config" in rules
    assert "ambíguo" in rules.lower() or "Ambíguo" in rules


def test_capability_surface_projects_live_agent_directives():
    surface = build_capability_surface()
    assert surface["rules"]["agent_directives_are_live"] is True
    assert surface["rules"]["builder_instructions_are_stable_only"] is True
    directives = surface["agent_directives"]
    assert directives["version"] == VistaAgentIntelligenceService.version()
    assert "object_resolution" in directives
    assert "modes" in directives
    assert "QUICK_DISPLAY" in directives["modes"]
    assert any("não consegue gravar" in str(item).lower() for item in directives["anti_patterns"])


def test_execution_posture_execute_typed_change_now():
    directives = VistaAgentIntelligenceService.agent_directives()
    posture = directives["execution_posture"]
    assert posture["principle"] == "EXECUTE_TYPED_CHANGE_NOW"
    rules = " ".join(posture["rules"]).lower()
    assert "mesmo turno" in rules or "neste turno" in rules
    assert "actions" in rules
    forbidden = " ".join(posture["forbidden"]).lower()
    assert "não disponíveis" in forbidden or "indispon" in forbidden
    assert "posso aplicar" in forbidden or any(
        "posso aplicar" in str(item).lower() for item in directives["anti_patterns"]
    )
    assert "same_turn" in directives["write_flow"]
    assert any(
        "não estão disponíveis" in str(item).lower() or "indispon" in str(item).lower()
        for item in directives["anti_patterns"]
    )


def test_visual_impact_tv_impact_first():
    directives = VistaAgentIntelligenceService.agent_directives()
    impact = directives["visual_impact"]
    assert impact["principle"] == "TV_IMPACT_FIRST"
    rules = " ".join(impact["rules"]).lower()
    assert "theme_delpi" in rules
    assert "area" in rules
    assert "banded" in rules
    stack = " ".join(impact["default_stack"]).lower()
    assert "hero" in stack
    assert any("impact" in str(item).lower() or "banded" in str(item).lower() for item in directives["anti_patterns"])
    tokens = directives["presentation_recipes"]["catalog"]["designTokens"]
    hints = tokens["visualImpactHints"]
    assert hints["temporalChartDefault"] == "area"
    assert hints["tablePresetDefault"] == "banded"
    assert tokens["chartTypeHints"]["temporal"][0] == "area"


def test_composed_visuals_compose_typed_blocks():
    from tv_app.application.services.data.presentation_recipe_service import (
        PresentationRecipeService,
        clear_presentation_recipes_cache,
    )
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
        clear_presentation_ops_content_cache,
    )

    clear_presentation_recipes_cache()
    clear_presentation_ops_content_cache()
    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    composed = directives["composed_visuals"]
    assert composed["principle"] == "COMPOSE_TYPED_BLOCKS"
    rules = " ".join(composed["rules"]).lower()
    assert "textprojection" in rules.replace(" ", "").replace("_", "")
    assert "groupid" in rules.replace(" ", "").replace("_", "")
    assert "COMPOSE_CUSTOM" in directives["modes"]
    recipe = PresentationRecipeService.get("TV_COMPOSED_DATA_CARD")
    assert recipe is not None
    ops = " ".join(str(op) for op in recipe.get("ops") or [])
    assert "shape" in ops and "textProjection" in ops
    assert "boxShadow" in ops and "borderRadius" in ops
    hints = directives["presentation_recipes"]["catalog"]["designTokens"]["visualImpactHints"]
    assert "text" in hints["composeWith"]
    assert "heading" in hints["textDataBinding"]["blockTypes"]
    spec = PresentationOpsContentService.operation_spec("upsert_block")
    assert spec is not None
    props = spec["inputSchema"]["properties"]["block"]["properties"]
    assert "textProjection" in props
    assert "contentRuns" in props
    style_props = props["style"]["properties"]
    assert "boxShadow" in style_props and "borderRadius" in style_props


def test_shape_chrome_combo():
    from tv_app.application.services.data.presentation_recipe_service import (
        clear_presentation_recipes_cache,
    )

    clear_presentation_recipes_cache()
    clear_vista_agent_intelligence_cache()
    directives = VistaAgentIntelligenceService.agent_directives()
    chrome = directives["shape_chrome"]
    assert chrome["principle"] == "SHAPE_CHROME_COMBO"
    assert "borderRadius" in chrome["style_keys"]
    assert "boxShadow" in chrome["style_keys"]
    assert "card_surface" in chrome["presets"]
    tokens = directives["presentation_recipes"]["catalog"]["designTokens"]["shapeChrome"]
    assert tokens["presets"]["card_surface"]["borderRadius"] == 16
    assert "elevated" in tokens["shadows"]
    assert any("flat" in str(item).lower() or "boxshadow" in str(item).lower() for item in directives["anti_patterns"])


def test_sibling_explicit_create_still_allowed_in_policy_text():
    rules = " ".join(
        VistaAgentIntelligenceService.agent_directives()["object_resolution"]["rules"]
    )
    assert "criação explícita" in rules.lower() or "pedir criação" in rules.lower()


def test_negative_duplicate_for_color_change_is_forbidden():
    rules = " ".join(
        VistaAgentIntelligenceService.agent_directives()["object_resolution"]["rules"]
    )
    assert "nunca add_blank_slide" in rules.lower() or "add_blank_slide" in rules


def test_screenshot_parity_maps_print_to_typed_slide():
    directives = VistaAgentIntelligenceService.agent_directives()
    parity = directives["screenshot_parity"]
    assert parity["principle"] == "PRINT_TO_TYPED_SLIDE_PARITY"
    assert "VISUAL_PARITY" in directives["modes"]
    pipeline = " ".join(parity["pipeline"])
    assert "upsert_block" in pipeline
    assert "patch_native_config" in pipeline
    assert "gpt_preview_change" in pipeline
    forbidden = " ".join(parity["parity_bar"]["forbidden_shortcuts"])
    assert "Image Generation" in forbidden or "imagem" in forbidden.lower()
    assert any("print" in str(item).lower() for item in directives["anti_patterns"])


def test_sibling_screenshot_does_not_authorize_uuid_invention():
    epi = " ".join(
        VistaAgentIntelligenceService.agent_directives()["screenshot_parity"]["epistemology"]
    )
    assert "nunca" in epi.lower()
    assert "playlistId" in epi or "slideId" in epi


def test_data_discovery_owner_local_no_dump():
    directives = VistaAgentIntelligenceService.agent_directives()
    discovery = directives["data_discovery"]
    assert discovery["principle"] == "OWNER_LOCAL_ROUTE_DISCOVERY"
    rules = " ".join(discovery["rules"])
    assert "query" in rules.lower()
    assert "paramSchema" in rules
    assert "searchMissDoesNotProveAbsence" in rules or "Miss" in rules
    assert "PRESENT_ALL_SEARCH_HITS" in rules
    assert "série" in rules.lower() or "series" in rules.lower()
    forbidden = " ".join(discovery["forbidden"])
    assert "omitir" in forbidden.lower() or "Omitir" in " ".join(directives["anti_patterns"])
    assert "dump" in forbidden.lower() or "Dump" in " ".join(directives["anti_patterns"])


def test_data_transform_typed_steps_only():
    directives = VistaAgentIntelligenceService.agent_directives()
    transform = directives["data_transform"]
    assert transform["principle"] == "TYPED_STEPS_ONLY"
    rules = " ".join(transform["rules"])
    assert "steps" in rules.lower()
    assert "merge" in rules.lower()
    forbidden = " ".join(transform["forbidden"])
    assert "script" in forbidden.lower() or "M" in forbidden
    assert any("script M" in str(item) or "steps tipados" in str(item) for item in directives["anti_patterns"])
    assert directives["compound_slide"]["principle"] == "READY_COMPOUND_SLIDE"
    assert directives["media_limits"]["principle"] == "ASSET_ID_ONLY"
