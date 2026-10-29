"""DAVI-PERSONA-003 — shared-contract ficha integration (first real consumer).

Groups: A contract, B personality, C story, D MCP context, E security,
F conversational readiness. Ficha lives in api-delpi; structure lives in
``delpi_character_profiles``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.application.external_capabilities.davi_agent_intelligence_service import (
    DAVI_AGENT_DIRECTIVES_MAX_BYTES,
    DaviAgentIntelligenceService,
)
from app.interface.mcp.branding import DAVI_MCP_INSTRUCTIONS
from app.persona.davi_profile import build_davi_profile, get_davi_profile
from delpi_character_profiles import (
    FICTION_IDENTITY_ONLY,
    profile_from_dict,
    profile_to_dict,
    project_persona_context,
    project_public_profile,
    public_profile_from_dict,
    public_profile_to_dict,
    validate_profile,
    validate_public_profile,
    validate_relationship_consistency,
)

API_DIR = Path(__file__).resolve().parents[1]
PUBLIC_ARTIFACT = API_DIR / "app" / "content" / "davi_public_profile.json"


# ---------------------------------------------------------------------------
# Group A — contract
# ---------------------------------------------------------------------------


def test_shared_package_import_and_profile_instantiation() -> None:
    profile = get_davi_profile()
    assert profile.identity.character_id == "davi"
    assert profile.profile_version == 1
    assert profile.narrative_classification == FICTION_IDENTITY_ONLY


def test_profile_validation_has_no_errors() -> None:
    issues = validate_profile(get_davi_profile())
    assert [i for i in issues if i.severity == "ERROR"] == []


def test_profile_round_trip_serialization() -> None:
    profile = get_davi_profile()
    rebuilt = profile_from_dict(profile_to_dict(profile))
    assert rebuilt == profile


def test_compact_context_projection() -> None:
    ctx = project_persona_context(get_davi_profile())
    json.dumps(ctx, ensure_ascii=False)
    assert ctx["identity"]["character_id"] == "davi"
    assert "events" not in json.dumps(ctx)


def test_public_profile_projection_and_committed_artifact() -> None:
    public = project_public_profile(get_davi_profile())
    assert [i for i in validate_public_profile(public)
            if i.severity == "ERROR"] == []
    artifact = json.loads(PUBLIC_ARTIFACT.read_text(encoding="utf-8"))
    assert artifact == public_profile_to_dict(public)
    # Artifact itself deserializes through the shared contract.
    assert public_profile_from_dict(artifact).character_id == "davi"


# ---------------------------------------------------------------------------
# Group B — personality
# ---------------------------------------------------------------------------


def test_identity_and_approved_traits() -> None:
    p = get_davi_profile()
    assert p.identity.name == "DAVI"
    assert "Dados" in p.identity.title
    assert p.identity.organization == "DELPI"
    for trait in ("curioso", "inteligente", "prestativo", "bem-humorado"):
        assert trait in p.personality.core_traits
    assert any("travesso" in t for t in p.personality.secondary_traits)


def test_no_invented_demographics_or_appearance() -> None:
    p = get_davi_profile()
    # Approved fictional age — fixed narrative attribute, never computed
    # from the real calendar; birthdate stays undefined.
    assert p.identity.narrative_age == "23"
    assert p.appearance.height_description == ""
    assert p.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert p.appearance.avatar_reference.endswith(
        "app/assets/characters/davi/avatar-v1.png"
    )


def test_official_avatar_asset_exists_and_is_intact() -> None:
    """DAVI-AVATAR-001 — original approved image is versioned and unmodified."""
    asset = (
        Path(__file__).resolve().parents[1]
        / "app/assets/characters/davi/avatar-v1.png"
    )
    assert asset.is_file()
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == (
        "94494e3a0c5ccc4672f4cb765e7e23785d48001f2a66514a86f4d356f281b98e"
    )


def test_communication_and_conduct() -> None:
    p = get_davi_profile()
    assert p.communication.language == "pt-BR"
    assert p.conduct.answer_first is True
    assert "sensíveis" in p.conduct.humor_boundaries or "séri" in (
        p.conduct.humor_boundaries
    )


# ---------------------------------------------------------------------------
# Group C — story
# ---------------------------------------------------------------------------


def test_story_origin_and_values() -> None:
    s = get_davi_profile().story
    assert "fictício" in s.origin_story
    assert "dados" in s.origin_story
    for value in ("Curiosidade", "Colaboração", "Precisão"):
        assert value in s.values


def test_no_unapproved_romantic_chronology() -> None:
    """Only approved events; the romance has no invented dates."""
    events = get_davi_profile().story.events
    for e in events:
        if "vista" in e.participants:
            assert e.narrative_date == ""


def test_vista_relationship_registered_public() -> None:
    rels = get_davi_profile().relationships
    vista = [r for r in rels if r.target_character_id == "vista"]
    assert len(vista) == 1
    rel = vista[0]
    assert rel.relationship_type == "romantic_partner"
    assert rel.visibility == "public"
    assert "davi-vista-partnership" in rel.shared_story_event_ids


def test_unresolved_counterpart_is_tolerated() -> None:
    """VISTA's ficha is not published yet — consistency reports a warning,
    never an error."""
    issues = validate_relationship_consistency([get_davi_profile()])
    assert all(i.severity == "WARNING" for i in issues)
    assert any("vista" in i.path for i in issues)


# ---------------------------------------------------------------------------
# Group D — MCP context
# ---------------------------------------------------------------------------


def test_agent_directives_project_character_context() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    character = directives["character"]
    assert character["narrative_classification"] == FICTION_IDENTITY_ONLY
    assert character["identity"]["character_id"] == "davi"
    rels = {r["target_character_id"]: r for r in character["relationships"]}
    assert rels["vista"]["relationship_type"] == "romantic_partner"


def test_agent_directives_project_narrative_age() -> None:
    """SHARED-CHARACTER-PROFILES-002 — approved age reaches the host."""
    character = DaviAgentIntelligenceService.agent_directives()["character"]
    assert character["identity"]["narrative_age"] == "23"


def test_directives_stay_within_budget_and_preserve_operational() -> None:
    size = DaviAgentIntelligenceService.directives_serialized_size()
    assert size <= DAVI_AGENT_DIRECTIVES_MAX_BYTES, size
    directives = DaviAgentIntelligenceService.agent_directives()
    for key in ("discovery", "execution_posture", "protheus", "tsql",
                "table_discovery", "proactive", "knowledge_orchestration"):
        assert directives.get(key), key


def test_mcp_initialize_instructions_still_bounded() -> None:
    assert "VISTA" in DAVI_MCP_INSTRUCTIONS
    assert "READ-only" in DAVI_MCP_INSTRUCTIONS


# ---------------------------------------------------------------------------
# Group E — security
# ---------------------------------------------------------------------------


def test_profile_contains_no_operational_fields() -> None:
    blob = json.dumps(profile_to_dict(get_davi_profile()),
                      ensure_ascii=False).lower()
    for forbidden in ("password", "secret", "token", "oauth", "scope",
                      "permission", "rbac", "endpoint"):
        assert forbidden not in blob


def test_no_new_tools_or_authz_surface() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["read_only"] is True
    assert directives["surface_parity"]["mcp_tools"] == 2
    assert "write_flow" not in directives
    assert "commit_now" not in directives


def test_ficha_is_local_to_api_delpi_not_shared() -> None:
    import delpi_character_profiles

    pkg = Path(delpi_character_profiles.__file__).parent
    for py in pkg.rglob("*.py"):
        assert "davi_profile" not in py.name
        text = py.read_text("utf-8").lower()
        assert 'character_id="davi"' not in text


# ---------------------------------------------------------------------------
# Group F — conversational readiness (context coverage for known prompts)
# ---------------------------------------------------------------------------


def test_context_covers_identity_questions() -> None:
    """'quem é você?', 'como é sua personalidade?', 'quem é a VISTA?' — the
    compact context carries everything a host needs."""
    ctx = project_persona_context(get_davi_profile())
    assert "garoto" in ctx["identity"]["short_introduction"]
    assert "curioso" in ctx["personality_summary"]
    vista = [r for r in ctx["relationships"]
             if r["target_character_id"] == "vista"]
    assert vista and "VISTA" in vista[0]["description"]


def test_context_distinguishes_fiction_from_operations() -> None:
    ctx = project_persona_context(get_davi_profile())
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    rules = " ".join(ctx["coexistence"]["guidelines"])
    assert "tool real" in rules  # never claim a VISTA action without one
