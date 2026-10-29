"""EVA character profile tests — EVA-CHARACTER-PROFILE-001.

Layers covered: ficha build (unit), shared-contract conformance
(contract), approved narrative facts (narrative), fiction-only/security
boundaries (security) and the get_catalog → agent_directives wiring
(integration). The profile grants no tool, permission or capability.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from delpi_character_profiles import (
    FICTION_IDENTITY_ONLY,
    RELATIONSHIP_TYPES,
    project_persona_context,
    project_public_profile,
    public_profile_from_dict,
    public_profile_to_dict,
    validate_profile,
    validate_relationship_consistency,
)

from engineering_app.application.eva.agent_intelligence_service import (
    EvaAgentIntelligenceService,
)
from engineering_app.persona.eva_profile import (
    AVATAR_PATH,
    get_eva_profile,
)

PROFILE = get_eva_profile()

# SHA-256 of the approved avatar asset (avatar-v1.jpg, 1024x1024).
APPROVED_AVATAR_SHA256 = (
    "18d9e05fc91388e236d3df6a8118634a604caeaf9dc0626bed4de240efc4e6fc"
)

APPROVED_RELATIONSHIPS = {
    "teo": "family",
    "delia": "narrative_partnership",
    "davi": "friendship",
    "vista": "friendship",
    "clara": "colleagues",
}

_MONOREPO_ROOT = Path(__file__).resolve().parents[2]
_PUBLIC_PROFILE_GLOBS = (
    "api-delpi/app/content/*_public_profile.json",
    "transformometro-api/tm_app/content/*_public_profile.json",
    "tv-dashboard-api/tv_app/content/*_public_profile.json",
    "controllership-finance-api/controllership_finance_app/content/"
    "*_public_profile.json",
)


def _sibling_public_profiles():
    """Public projections published by sibling MCPs (monorepo layout)."""
    found = []
    for pattern in _PUBLIC_PROFILE_GLOBS:
        for path in _MONOREPO_ROOT.glob(pattern):
            try:
                found.append(
                    public_profile_from_dict(
                        json.loads(path.read_text(encoding="utf-8"))
                    )
                )
            except (OSError, ValueError, KeyError):
                continue
    return found


# --- unit: ficha build ----------------------------------------------------


def test_identity_is_eva_engineering():
    i = PROFILE.identity
    assert i.character_id == "eva"
    assert i.name == "EVA"
    assert i.display_name == "EVA — Engenharia Virtual Assistida"
    assert i.organization == "DELPI"
    assert i.gender_identity == "feminina"
    assert PROFILE.universe.startswith("Especialistas DELPI")


def test_narrative_age_is_29():
    assert PROFILE.identity.narrative_age == "29 anos"
    assert "29 anos" in PROFILE.appearance.age_appearance


def test_short_introduction_matches_approved_copy():
    assert PROFILE.identity.short_introduction == (
        "Olá! Eu sou a EVA, especialista em Engenharia da DELPI. "
        "Gosto de compreender como as coisas funcionam, "
        "investigar detalhes técnicos e ajudar a transformar "
        "informações complexas em soluções claras e fundamentadas."
    )


def test_approved_personality_traits():
    for trait in (
        "curiosa",
        "analítica",
        "inventiva",
        "observadora",
        "inteligente",
        "colaborativa",
        "responsável",
        "carinhosa",
        "didática",
    ):
        assert trait in PROFILE.personality.core_traits


def test_story_sections_present_and_consistent():
    s = PROFILE.story
    assert s.origin_story
    assert s.personal_mission
    assert s.current_story_arc
    assert "TÉO" in s.current_story_arc
    assert "precisão" in s.values
    assert "engenharia" in s.interests


def test_no_invented_shared_events():
    """Events never claim participation of characters without an
    approved shared story — participants stay within this ficha."""
    for ev in PROFILE.story.events:
        assert ev.participants == ("eva",)
        for rel in PROFILE.relationships:
            assert rel.target_character_id not in ev.participants


# --- narrative: appearance / avatar ---------------------------------------


def test_eva_never_wears_glasses():
    assert PROFILE.appearance.glasses == ""
    summary = project_persona_context(PROFILE)["appearance_summary"]
    assert "óculos" not in summary.lower()
    assert "glasses" not in summary.lower()


def test_appearance_matches_approved_visual():
    a = PROFILE.appearance
    assert "castanhos" in a.hair and "ondulados" in a.hair
    assert "castanhos" in a.eyes
    assert "azul-marinho" in a.clothing
    assert "3D" in a.visual_style or "cinematográf" in a.visual_style


def test_avatar_official_and_asset_integrity():
    a = PROFILE.appearance
    assert a.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert a.avatar_reference == (
        "engineering_app/assets/characters/eva/avatar-v1.jpg"
    )
    assert AVATAR_PATH.is_file()
    assert hashlib.sha256(AVATAR_PATH.read_bytes()).hexdigest() == (
        APPROVED_AVATAR_SHA256
    )


def test_avatar_status_degrades_when_asset_missing(tmp_path, monkeypatch):
    """No official status may be claimed without the asset on disk."""
    from engineering_app.persona import eva_profile as module

    monkeypatch.setattr(module, "AVATAR_PATH", tmp_path / "missing.jpg")
    p = module.build_eva_profile()
    assert p.appearance.avatar_status == "REFERENCE_NOT_OFFICIAL_AVATAR"


# --- narrative: relationships ---------------------------------------------


def test_exactly_the_five_approved_relationships():
    actual = {
        r.target_character_id: r.relationship_type
        for r in PROFILE.relationships
    }
    assert actual == APPROVED_RELATIONSHIPS


def test_relationship_types_are_approved_vocabulary():
    for r in PROFILE.relationships:
        assert r.relationship_type in RELATIONSHIP_TYPES
        assert r.visibility == "public"


def test_family_relationship_is_younger_brother_teo():
    teo = next(
        r for r in PROFILE.relationships if r.target_character_id == "teo"
    )
    assert teo.relationship_type == "family"
    assert "irmão mais novo" in teo.description


def test_relationship_consistency_vs_siblings_is_warning_free_of_errors():
    """Missing reciprocal edges are WARNINGs (fichas deploy
    independently); contradictions (ERROR) are never tolerated."""
    siblings = _sibling_public_profiles()
    issues = validate_relationship_consistency([PROFILE, *siblings])
    assert all(i.severity != "ERROR" for i in issues)


# --- contract: shared package ----------------------------------------------


def test_profile_validates_clean():
    assert validate_profile(PROFILE) == []


def test_narrative_classification_is_fiction_only():
    assert PROFILE.narrative_classification == FICTION_IDENTITY_ONLY


def test_persona_context_projection_shape():
    ctx = project_persona_context(PROFILE)
    assert ctx["identity"]["character_id"] == "eva"
    assert ctx["identity"]["narrative_age"] == "29 anos"
    assert ctx["avatar_status"] == "OFFICIAL_AVATAR_APPROVED"
    rels = {r["target_character_id"] for r in ctx["relationships"]}
    assert rels == set(APPROVED_RELATIONSHIPS)


def test_public_profile_exposes_no_internals():
    pub = project_public_profile(PROFILE)
    data = public_profile_to_dict(pub)
    serialized = json.dumps(data, ensure_ascii=False)
    for forbidden in ("permission", "token", "secret", "keycloak"):
        assert forbidden not in serialized.lower()
    assert all(
        r.visibility == "public" for r in pub.relationships
    )


def test_committed_public_profile_file_is_current():
    path = (
        Path(__file__).resolve().parents[1]
        / "engineering_app"
        / "content"
        / "eva_public_profile.json"
    )
    committed = json.loads(path.read_text(encoding="utf-8"))
    assert committed == public_profile_to_dict(
        project_public_profile(PROFILE)
    )


# --- integration: get_catalog wiring ---------------------------------------


def test_agent_directives_carry_persona_context():
    d = EvaAgentIntelligenceService.agent_directives()
    character = d["character"]
    assert character["identity"]["character_id"] == "eva"
    assert character["identity"]["name"] == "EVA"
    assert character["narrative_classification"] == FICTION_IDENTITY_ONLY


def test_get_catalog_exposes_agent_directives():
    from engineering_app.interface.mcp import tool_bridge

    monkey_ctx = pytest.MonkeyPatch()
    monkey_ctx.setattr(
        tool_bridge, "_require_engineering_human", lambda: object()
    )
    try:
        result = tool_bridge.tool_get_catalog()
    finally:
        monkey_ctx.undo()
    payload = json.loads(result.content[0].text)
    directives = payload["data"]["agent_directives"]
    assert directives["character"]["identity"]["character_id"] == "eva"


# --- security: fiction-only boundaries -------------------------------------


def test_intelligence_document_grants_no_operational_surface():
    doc = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "engineering_app"
            / "content"
            / "eva_agent_intelligence.json"
        ).read_text(encoding="utf-8")
    )
    assert doc["narrative"]["type"] == FICTION_IDENTITY_ONLY
    forbidden_keys = {"permissions", "scopes", "tools", "grants", "credentials"}
    for section in ("identity", "narrative", "story"):
        assert not forbidden_keys & set(doc[section].keys())
