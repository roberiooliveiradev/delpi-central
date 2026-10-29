"""CHARACTER-PROFILE-TEO-001 — TÉO ficha via delpi_character_profiles.

Shared owns the structure; transformometro-api owns the TÉO profile.
Fiction only: the ficha never grants tools, permissions or authority.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from delpi_character_profiles import (
    public_profile_from_dict,
    public_profile_to_dict,
    validate_profile,
    validate_relationship_consistency,
)

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
    clear_teo_agent_intelligence_cache,
)

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parent


def setup_function() -> None:
    clear_teo_agent_intelligence_cache()


def teardown_function() -> None:
    clear_teo_agent_intelligence_cache()


def _profile():
    return TeoAgentIntelligenceService.character_profile()


def test_profile_builds_and_validates_without_errors():
    issues = validate_profile(_profile())
    errors = [i for i in issues if i.severity == "ERROR"]
    assert errors == []
    # No warnings are accepted silently — keep this strict.
    assert [i for i in issues if i.severity == "WARNING"] == []


def test_identity_fields():
    ident = _profile().identity
    assert ident.character_id == "teo"
    assert ident.name == "TÉO"
    assert ident.display_name == "TÉO — Especialista em Transformação Digital"
    assert ident.title == "O Jovem Gênio da Inovação"
    assert ident.organization == "DELPI"
    assert ident.narrative_age == "16"
    assert ident.gender_identity == "masculino"
    assert ident.pronouns == "ele/dele"
    assert "jovem inventor digital" in ident.short_introduction


def test_appearance_is_reference_not_official_avatar():
    app = _profile().appearance
    assert app.avatar_status == "REFERENCE_NOT_OFFICIAL_AVATAR"
    assert "16" in app.age_appearance
    assert app.hair
    assert app.clothing
    assert set(app.color_palette) >= {"azul", "turquesa", "laranja"}


def test_personality_traits_and_humor_bounds():
    p = _profile().personality
    traits = " ".join(p.core_traits).lower()
    for marker in ("curioso", "perspicaz", "inventivo", "bem-humorado"):
        assert marker in traits, marker
    assert "nunca" in p.humor_style
    # Neurodivergence is an inspiration reference, never a diagnosis.
    blob = json.dumps(_profile().personality.__dict__, ensure_ascii=False)
    assert "TEA" not in blob
    assert "altas habilidades" not in blob


def test_communication_style():
    c = _profile().communication
    assert c.language == "pt-BR"
    assert c.humor_frequency
    assert c.preferred_expressions  # voice examples, non-mandatory


def test_expertise_is_narrative_not_tools():
    e = _profile().expertise
    assert e.specialties
    blob = " ".join(e.specialties + e.knowledge_domains).lower()
    for forbidden in ("tool", "permission", "credential", "endpoint", "gpt_"):
        assert forbidden not in blob, forbidden


def test_story_and_approved_events():
    s = _profile().story
    assert "16" in s.origin_story
    assert s.personal_mission
    assert s.current_story_arc
    ids = {e.event_id for e in s.events}
    assert ids == {
        "teo-origin",
        "teo-joins-minha-delpi",
        "teo-tech-investigator",
        "teo-innovation-journey",
    }
    # No invented real dates on narrative events.
    assert all(not e.narrative_date for e in s.events)


def test_relationships_davi_and_vista_are_public_colleagues():
    rels = {r.target_character_id: r for r in _profile().relationships}
    assert set(rels) == {"davi", "vista"}
    for r in rels.values():
        assert r.relationship_type == "colleagues"
        assert r.visibility == "public"
    # TÉO has no romantic/family relationships — none approved.
    types = {r.relationship_type for r in _profile().relationships}
    assert "romantic_partner" not in types
    assert "family" not in types


def test_coexistence_and_conduct_preserve_boundaries():
    rules = _profile().coexistence
    assert rules.mention_frequency == "occasional"
    blob = " ".join(rules.forbidden_behaviors)
    assert "comunicação real" in blob
    assert "evidência operacional" in blob
    conduct = _profile().conduct
    assert conduct.answer_first is True
    assert conduct.humor_boundaries


def test_narrative_classification_is_fiction_only():
    assert _profile().narrative_classification == "FICTION_IDENTITY_ONLY"
    assert _profile().universe.startswith("Especialistas DELPI")


def test_persona_context_projection():
    ctx = TeoAgentIntelligenceService.persona_context()
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    assert ctx["identity"]["character_id"] == "teo"
    assert ctx["identity"]["narrative_age"] == "16"
    assert ctx["avatar_status"] == "REFERENCE_NOT_OFFICIAL_AVATAR"
    assert ctx["appearance_summary"]
    assert ctx["personality_summary"]
    rel_ids = {r["target_character_id"] for r in ctx["relationships"]}
    assert rel_ids == {"davi", "vista"}
    # Bounded context payload.
    size = len(json.dumps(ctx, ensure_ascii=True).encode("utf-8"))
    assert size < 8_000


def test_public_profile_excludes_internals_and_operational_data():
    pub = TeoAgentIntelligenceService.public_profile()
    payload = public_profile_to_dict(pub)
    blob = json.dumps(payload).lower()
    for forbidden in (
        "password",
        "token",
        "permission",
        "scope",
        "gpt_",
        "endpoint",
        "internal",
    ):
        assert forbidden not in blob, forbidden
    assert payload["character_id"] == "teo"
    assert payload["public_projection_version"] >= 1
    # Committed artifact matches the live projection.
    artifact = json.loads(
        (APP_ROOT / "tm_app" / "content" / "teo_public_profile.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact == payload


def test_public_projection_roundtrip_serialization():
    pub = TeoAgentIntelligenceService.public_profile()
    restored = public_profile_from_dict(public_profile_to_dict(pub))
    assert restored.character_id == "teo"
    assert restored.relationships == pub.relationships


def _load_public_artifact(relative: str):
    path = REPO_ROOT / relative
    if not path.exists():
        return None
    return public_profile_from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def test_relationship_consistency_with_published_profiles():
    """Cross-check against committed public profiles (DAVI/VISTA).

    ``colleagues`` expects a reciprocal edge; DAVI/VISTA fichas predate
    TÉO and do not declare one — the contract reports WARNING, never
    ERROR. Warnings are documented; only contradictions fail.
    """
    profiles = [TeoAgentIntelligenceService.public_profile()]
    for rel in (
        "api-delpi/app/content/davi_public_profile.json",
        "tv-dashboard-api/tv_app/content/vista_public_profile.json",
    ):
        loaded = _load_public_artifact(rel)
        if loaded is not None:
            profiles.append(loaded)
    issues = validate_relationship_consistency(profiles)
    assert [i for i in issues if i.severity == "ERROR"] == []
    # DAVI–VISTA romantic relationship is preserved on both sides.
    by_id = {
        p.character_id: p for p in profiles if p.character_id != "teo"
    }
    if "davi" in by_id and "vista" in by_id:
        davi_types = {
            r.relationship_type
            for r in by_id["davi"].relationships
            if r.target_character_id == "vista"
        }
        vista_types = {
            r.relationship_type
            for r in by_id["vista"].relationships
            if r.target_character_id == "davi"
        }
        assert "romantic_partner" in davi_types
        assert "romantic_partner" in vista_types


def test_agent_directives_integrate_character_on_both_transports():
    for transport in ("gpt_actions", "mcp"):
        directives = TeoAgentIntelligenceService.agent_directives(
            transport=transport
        )
        ch = directives.get("character") or {}
        assert ch["identity"]["character_id"] == "teo", transport
        assert ch["identity"]["narrative_age"] == "16", transport
        # Operational directives are preserved — narrative never replaces
        # discovery, write-flow or execution posture.
        assert directives.get("discovery"), transport
        assert directives.get("execution_posture"), transport
        if transport == "mcp":
            assert "gpt_" not in json.dumps(ch)
            assert directives.get("write_flow_mcp")
        else:
            assert directives.get("write_flow")


def test_character_never_appears_as_capability():
    surface = build_capability_surface_catalog()
    names = json.dumps(
        surface.get("capabilities") or surface.get("tools") or {}
    ).lower()
    for forbidden in ("persona", "character", "story", "narrative"):
        assert forbidden not in names, forbidden


def test_directives_stay_under_compaction_threshold():
    from tm_app.application.gpt_actions.response_compact import (
        ascii_utf8_size,
    )

    directives = TeoAgentIntelligenceService.agent_directives(
        transport="gpt_actions"
    )
    # Guard: character + identity must fit the bound that skips the
    # destructive fallback (which would drop discovery/solutions/flows).
    assert ascii_utf8_size(directives) <= 45_000
