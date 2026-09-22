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
