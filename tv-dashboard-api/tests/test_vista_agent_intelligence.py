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
