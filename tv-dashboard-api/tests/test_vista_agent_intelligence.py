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
    assert "conector" in rules or "actions_runtime" in rules
    forbidden = " ".join(posture["forbidden"]).lower()
    assert "não disponíveis" in forbidden or "indispon" in forbidden or "conector" in forbidden
    assert "posso aplicar" in forbidden or any(
        "posso aplicar" in str(item).lower() for item in directives["anti_patterns"]
    )
    assert "same_turn" in directives["write_flow"]
    assert any(
        "não estão disponíveis" in str(item).lower()
        or "indispon" in str(item).lower()
        or "conector" in str(item).lower()
        for item in directives["anti_patterns"]
    )


def test_actions_runtime_try_before_claiming_unavailable():
    directives = VistaAgentIntelligenceService.agent_directives()
    runtime = directives["actions_runtime"]
    assert runtime["principle"] == "TRY_ACTION_BEFORE_CLAIMING_UNAVAILABLE"
    rules = " ".join(runtime["rules"]).lower()
    assert "gpt_get_catalog" in rules
    assert "conector" in rules
    assert "tentar" in rules or "tente" in rules
    forbidden = " ".join(runtime["forbidden"]).lower()
    assert "conector" in forbidden
    assert "sem ter tentado" in forbidden or "sem tentativa" in " ".join(runtime["rules"]).lower()
    auth = directives["auth_errors"]
    assert "never_without_attempt" in auth
    assert "tool_unavailable_after_attempt" in auth
    # Priority: connector anti-patterns must survive the anti_patterns compact cap.
    joined = " ".join(str(item).lower() for item in directives["anti_patterns"][:8])
    assert "conector" in joined


def test_visual_impact_tv_impact_first():
    directives = VistaAgentIntelligenceService.agent_directives()
    impact = directives["visual_impact"]
    assert impact["principle"] == "TV_IMPACT_FIRST"
    rules = " ".join(impact["rules"]).lower()
    assert "theme_delpi" in rules
    assert "visual_selection" in rules
    assert "area" in rules
    assert "banded" in rules
    stack = " ".join(impact["default_stack"]).lower()
    assert "hero" in stack or "sinal hero" in stack
    assert "visual_selection" in stack or "charttypehints" in stack.replace(" ", "")
    assert any("impact" in str(item).lower() or "banded" in str(item).lower() for item in directives["anti_patterns"])
    tokens = directives["presentation_recipes"]["catalog"]["designTokens"]
    hints = tokens["visualImpactHints"]
    assert hints["temporalChartDefault"] == "area"
    assert hints["tablePresetDefault"] == "banded"
    assert hints.get("shapeFollowsData") is True
    assert tokens["chartTypeHints"]["temporal"][0] == "area"
    assert "horizontal_bar" in tokens["chartTypeHints"]["categorical"]
    assert "TV_TABLE_FOCUS" in hints["preferRecipes"]
    assert "TV_FILTER_STRIP" in hints["preferRecipes"]


def test_visual_selection_shape_follows_data():
    directives = VistaAgentIntelligenceService.agent_directives()
    vs = directives["visual_selection"]
    assert vs["principle"] == "SHAPE_FOLLOWS_DATA"
    types = vs["catalog_chart_types"]
    for required in ("area", "bar", "horizontal_bar", "pie", "funnel", "gauge", "combo"):
        assert required in types
    table = " ".join(
        f"{row.get('when', '')} {' '.join(row.get('prefer') or [])}"
        for row in vs.get("decision_table") or []
    ).lower()
    assert "categór" in table or "categor" in table
    assert "bar" in table
    assert "ranking" in table or "table" in table
    rules = " ".join(vs["rules"]).lower()
    assert "kpi" in rules and ("área" in rules or "area" in rules)
    forbidden = " ".join(vs["forbidden"]).lower()
    assert "kpi" in forbidden and ("área" in forbidden or "area" in forbidden)
    assert "VISUAL_SELECTION" in directives["modes"]
    assert any(
        "visual_selection" in str(item).lower() or "kpi+área" in str(item).lower() or "kpi+area" in str(item).lower()
        for item in directives["anti_patterns"]
    )
    craft = directives["slide_craft"]
    checklist = " ".join(craft.get("checklist_before_verified") or []).lower()
    assert "forma-do-dado" in checklist or "kpi+área" in checklist or "kpi+area" in checklist


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
    # Full shapeChrome tokens stay in presentation_recipes.json (not GPT catalog — budget).
    from tv_app.application.services.data.presentation_recipe_service import (
        PresentationRecipeService,
    )

    tokens = PresentationRecipeService.catalog_projection()["designTokens"]["shapeChrome"]
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
    rules = " ".join(transform["rules"]).lower()
    assert "set_data_transform" in rules or "steps" in rules
    assert "mforbidden" in rules.replace(" ", "") or "m/" in rules or "script" in rules
    rules_raw = " ".join(transform["rules"])
    assert "steps" in rules_raw.lower()
    assert "merge" in rules_raw.lower()
    forbidden = " ".join(transform["forbidden"])
    assert "script" in forbidden.lower() or "M" in forbidden
    assert any("script M" in str(item) or "steps tipados" in str(item) for item in directives["anti_patterns"])
    assert directives["compound_slide"]["principle"] == "READY_COMPOUND_SLIDE"
    assert directives["media_limits"]["principle"] == "ASSET_ID_ONLY"


def test_filter_layering_and_slide_craft():
    directives = VistaAgentIntelligenceService.agent_directives()
    fl = directives["filter_layering"]
    assert fl["principle"] == "LAYERED_FILTERS_MOST_SPECIFIC_WINS"
    merge = " ".join(fl["merge_order"]).lower()
    assert "datadefaults" in merge.replace(" ", "").replace("_", "")
    assert "datafilters" in merge.replace(" ", "").replace("_", "")
    dates = " ".join(fl["dates"]["prefer"] + fl["dates"]["forbidden"]).lower()
    assert "daterangepreset" in dates.replace(" ", "").replace("_", "")
    assert "hardcod" in dates or "absoluto" in dates
    craft = directives["slide_craft"]
    assert craft["principle"] == "ONE_DECISION_TV_SLIDE"
    craft_rules = " ".join(craft["rules"])
    assert "add_blank_slide" in craft_rules
    assert "create_slide" not in craft_rules
    assert "FILTER_LAYERING" in directives["modes"]
    assert any(
        "datadefaults" in str(item).lower().replace(" ", "").replace("_", "")
        or "hardcod" in str(item).lower()
        for item in directives["anti_patterns"]
    )


def test_continuous_review_always_review_existing():
    directives = VistaAgentIntelligenceService.agent_directives()
    review = directives["continuous_review"]
    assert review["principle"] == "ALWAYS_REVIEW_EXISTING"
    pipeline = " ".join(review["pipeline"]).lower()
    assert "layoutDigest".lower() in pipeline.replace(" ", "") or "layoutdigest" in pipeline.replace(" ", "")
    assert "existente" in " ".join(review["rules"]).lower() or "existing" in " ".join(review["rules"]).lower()
    assert "CONTINUOUS_REVIEW" in directives["modes"]
    posture = " ".join(directives["execution_posture"]["rules"]).lower()
    assert "continuous_review" in posture
    assert any(
        "existente" in str(item).lower() and ("novo" in str(item).lower() or "montar" in str(item).lower())
        for item in directives["anti_patterns"]
    )
