"""VISTA-PERSONA-001 — shared-contract ficha integration.

Groups: A contract, B personality, C story, D MCP context, E security,
F conversational readiness. Ficha lives in tv-dashboard-api; structure
lives in ``delpi_character_profiles``.
"""

from __future__ import annotations

import json
from pathlib import Path

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
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
)
from tv_app.persona.vista_profile import build_vista_profile, get_vista_profile

API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = API_DIR.parent
PUBLIC_ARTIFACT = API_DIR / "tv_app" / "content" / "vista_public_profile.json"
# Approved public projection published by the DAVI bounded context — used
# here only as test-time evidence for reciprocity, never a runtime import.
DAVI_PUBLIC_ARTIFACT = (
    REPO_ROOT / "api-delpi" / "app" / "content" / "davi_public_profile.json"
)


# ---------------------------------------------------------------------------
# Group A — contract
# ---------------------------------------------------------------------------


def test_shared_package_import_and_profile_instantiation() -> None:
    profile = get_vista_profile()
    assert profile.identity.character_id == "vista"
    # v2: avatar oficial aprovado (VISTA-AVATAR-001).
    assert profile.profile_version == 2
    assert profile.narrative_classification == FICTION_IDENTITY_ONLY


def test_profile_validation_has_no_errors() -> None:
    issues = validate_profile(get_vista_profile())
    assert [i for i in issues if i.severity == "ERROR"] == []


def test_profile_round_trip_serialization() -> None:
    profile = get_vista_profile()
    rebuilt = profile_from_dict(profile_to_dict(profile))
    assert rebuilt == profile


def test_profile_builds_from_canonical_content_document() -> None:
    """The ficha is composed from vista_agent_intelligence.json — no second
    prose source."""
    profile = build_vista_profile()
    doc = VistaAgentIntelligenceService.document()
    assert doc.get("persona", {}).get("narrative_age") == "20"
    assert doc.get("narrative", {}).get("type") == FICTION_IDENTITY_ONLY
    assert profile.identity.short_introduction == doc["persona"]["identity"]
    assert profile == get_vista_profile()


def test_compact_context_projection() -> None:
    ctx = project_persona_context(get_vista_profile())
    json.dumps(ctx, ensure_ascii=False)
    assert ctx["identity"]["character_id"] == "vista"
    # Full story/events stay out of the compact context (budget).
    assert "events" not in json.dumps(ctx)
    assert "origin_story" not in json.dumps(ctx)


def test_public_profile_projection_and_committed_artifact() -> None:
    public = project_public_profile(get_vista_profile())
    assert [
        i for i in validate_public_profile(public) if i.severity == "ERROR"
    ] == []
    artifact = json.loads(PUBLIC_ARTIFACT.read_text(encoding="utf-8"))
    assert artifact == public_profile_to_dict(public)
    # Artifact itself deserializes through the shared contract.
    assert public_profile_from_dict(artifact).character_id == "vista"


# ---------------------------------------------------------------------------
# Group B — personality
# ---------------------------------------------------------------------------


def test_identity_and_approved_traits() -> None:
    p = get_vista_profile()
    assert p.identity.name == "VISTA"
    assert p.identity.display_name == "VISTA — Painéis Operacionais DELPI"
    assert p.identity.organization == "DELPI"
    assert "painéis" in p.identity.role.lower()
    assert p.identity.gender_identity == "feminino"
    for trait in (
        "observadora",
        "criativa",
        "inteligente",
        "organizada",
        "proativa",
    ):
        assert trait in p.personality.core_traits
    for trait in ("competente", "detalhista", "comunicativa"):
        assert trait in p.personality.secondary_traits


def test_no_invented_demographics_or_appearance() -> None:
    p = get_vista_profile()
    # Approved fictional age — fixed narrative attribute, never computed
    # from the real calendar; birthdate stays undefined.
    assert p.identity.narrative_age == "20"
    assert p.appearance.age_appearance == "jovem — 20 anos"
    assert "pretos e lisos" in p.appearance.hair
    assert p.appearance.skin == "clara"
    assert p.appearance.glasses
    # VISTA-AVATAR-001 — approved official avatar reference.
    assert p.appearance.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    # Unapproved physical attributes stay empty.
    assert p.appearance.height_description == ""
    assert p.appearance.build == ""


def test_avatar_asset_persisted_and_resolvable() -> None:
    """The approved avatar is the original task-provided PNG, stored in the
    VISTA bounded context and resolvable from the ficha."""
    import hashlib

    p = get_vista_profile()
    ref = p.appearance.avatar_reference
    assert ref == "tv_app/content/characters/vista/avatar-v1.png"
    asset = API_DIR / ref
    assert asset.is_file(), ref
    blob = asset.read_bytes()
    # PNG magic + original file SHA-256 (byte-identical preservation).
    assert blob[:4] == b"\x89PNG"
    assert hashlib.sha256(blob).hexdigest() == (
        "740f772b66fbea4442342adb783f77539d554816da0ed8c40dfed39fdb0942b6"
    )


def test_communication_and_conduct() -> None:
    p = get_vista_profile()
    assert p.communication.language == "pt-BR"
    assert p.conduct.answer_first is True
    assert "sensíveis" in p.conduct.humor_boundaries
    assert "ambiguidades" in p.conduct.clarification_preferences


# ---------------------------------------------------------------------------
# Group C — story
# ---------------------------------------------------------------------------


def test_story_origin_and_values() -> None:
    s = get_vista_profile().story
    assert "fictício" in s.origin_story
    assert "visuais" in s.origin_story
    for value in ("Criatividade", "Clareza", "Organização"):
        assert value in s.values
    assert "Visualização de dados" in s.interests


def test_no_unapproved_romantic_chronology() -> None:
    """Only approved events; the romance has no invented dates."""
    events = get_vista_profile().story.events
    for e in events:
        if "davi" in e.participants:
            assert e.narrative_date == ""


def test_davi_relationship_registered_public() -> None:
    rels = get_vista_profile().relationships
    davi = [r for r in rels if r.target_character_id == "davi"]
    assert len(davi) == 1
    rel = davi[0]
    assert rel.relationship_type == "romantic_partner"
    assert rel.visibility == "public"
    # Canonical shared event published by DAVI's ficha — referenced, not
    # invented.
    assert "davi-vista-partnership" in rel.shared_story_event_ids


def test_davi_vista_reciprocity_against_public_artifact() -> None:
    """DAVI's approved public projection is published — reciprocity must be
    ERROR-free both against the full ficha and the public projection."""
    assert DAVI_PUBLIC_ARTIFACT.exists(), (
        "davi_public_profile.json missing — cannot verify reciprocity"
    )
    davi_public = public_profile_from_dict(
        json.loads(DAVI_PUBLIC_ARTIFACT.read_text(encoding="utf-8"))
    )
    vista = get_vista_profile()
    for candidates in ([vista, davi_public],
                       [project_public_profile(vista), davi_public]):
        issues = validate_relationship_consistency(candidates)
        assert [i for i in issues if i.severity == "ERROR"] == []


# ---------------------------------------------------------------------------
# Group D — MCP context
# ---------------------------------------------------------------------------


def test_agent_directives_project_character_context_on_mcp() -> None:
    directives = VistaAgentIntelligenceService.agent_directives(
        transport="mcp"
    )
    character = directives["character"]
    assert character["narrative_classification"] == FICTION_IDENTITY_ONLY
    assert character["identity"]["character_id"] == "vista"
    # SHARED-CHARACTER-PROFILES-002 projects narrative_age into identity.
    assert character["identity"]["narrative_age"] == "20"
    assert "20" in character["appearance_summary"]
    rels = {r["target_character_id"]: r
            for r in character["relationships"]}
    assert rels["davi"]["relationship_type"] == "romantic_partner"


def test_character_context_is_mcp_primary_not_actions() -> None:
    """The ~100 KiB Actions envelope has no residual budget — ``character``
    ships on the MCP transport only (same rule as ``surface_parity`` /
    ``write_flow_mcp`` / ``param_expressions``); stable persona lives in the
    Builder Instructions paste."""
    actions = VistaAgentIntelligenceService.agent_directives(
        transport="actions"
    )
    assert "character" not in actions
    mcp = VistaAgentIntelligenceService.agent_directives(transport="mcp")
    assert mcp["character"]["identity"]["character_id"] == "vista"


def test_directives_preserve_operational_surface() -> None:
    """Character context is additive — no operational section was removed."""
    directives = VistaAgentIntelligenceService.agent_directives()
    for key in (
        "knowledge_orchestration",
        "object_resolution",
        "write_flow_mcp",
        "surface_parity",
        "design_methodology",
        "data_model",
        "presentation_recipes",
        "auth_errors",
    ):
        assert directives.get(key), key


def test_directives_preserve_actions_operational_surface() -> None:
    directives = VistaAgentIntelligenceService.agent_directives(
        transport="actions"
    )
    for key in (
        "knowledge_orchestration",
        "object_resolution",
        "write_flow",
        "design_methodology",
        "data_model",
        "auth_errors",
    ):
        assert directives.get(key), key


# ---------------------------------------------------------------------------
# Group E — security
# ---------------------------------------------------------------------------


def test_profile_contains_no_operational_fields() -> None:
    blob = json.dumps(
        profile_to_dict(get_vista_profile()), ensure_ascii=False
    ).lower()
    for forbidden in ("password", "secret", "token", "oauth", "scope",
                      "permission", "rbac", "endpoint"):
        assert forbidden not in blob


def test_public_profile_carries_only_approved_narrative() -> None:
    blob = json.dumps(
        public_profile_to_dict(project_public_profile(get_vista_profile())),
        ensure_ascii=False,
    ).lower()
    for forbidden in ("password", "secret", "token", "oauth", "scope",
                      "permission", "rbac", "endpoint", "infra"):
        assert forbidden not in blob


def test_no_new_tools_or_authz_surface() -> None:
    """Ficha is narrative only: tool surface, write flow and AuthZ posture
    are untouched."""
    from tv_app.application.gpt_actions.openapi_builder import (
        GPT_ACTIONS_OPERATION_IDS,
    )

    assert len(GPT_ACTIONS_OPERATION_IDS) == 12
    directives = VistaAgentIntelligenceService.agent_directives(
        transport="mcp"
    )
    assert directives["character"]["narrative_classification"] == (
        FICTION_IDENTITY_ONLY
    )
    # Character must not smuggle capability/permission language.
    blob = json.dumps(directives["character"], ensure_ascii=False).lower()
    for forbidden in ("permission", "rbac", "oauth", "token"):
        assert forbidden not in blob


def test_ficha_is_local_to_tv_dashboard_not_shared() -> None:
    import delpi_character_profiles

    pkg = Path(delpi_character_profiles.__file__).parent
    for py in pkg.rglob("*.py"):
        assert "vista_profile" not in py.name
        text = py.read_text("utf-8").lower()
        assert 'character_id="vista"' not in text


# ---------------------------------------------------------------------------
# Group F — conversational readiness (context coverage for known prompts)
# ---------------------------------------------------------------------------


def test_context_covers_identity_questions() -> None:
    """'quem é você?', 'quantos anos?', 'como você é?', 'sua especialidade?',
    'tem namorado?', 'quem é o DAVI?' — the compact context carries
    everything a host needs."""
    ctx = project_persona_context(get_vista_profile())
    intro = ctx["identity"]["short_introduction"]
    assert "VISTA" in intro and "painéis" in intro
    assert "20" in ctx["appearance_summary"]
    assert "óculos" in ctx["appearance_summary"]
    # VISTA-AVATAR-001 — official avatar exposed via the shared context
    # projection as a stable repo-local reference (no base64, no URL).
    assert ctx["avatar_status"] == "OFFICIAL_AVATAR_APPROVED"
    assert ctx["avatar_reference"] == "tv_app/content/characters/vista/avatar-v1.png"
    assert "observadora" in ctx["personality_summary"]
    assert "visualização" in " ".join(
        ctx["expertise"]["specialties"]
    ).lower() or "Visualização" in " ".join(ctx["expertise"]["specialties"])
    davi = [r for r in ctx["relationships"]
            if r["target_character_id"] == "davi"]
    assert davi and "namorado" in davi[0]["description"]


def test_context_distinguishes_fiction_from_operations() -> None:
    ctx = project_persona_context(get_vista_profile())
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    rules = " ".join(ctx["coexistence"]["guidelines"])
    assert "evidência" in rules  # never claim a DAVI action without one
    forbidden = " ".join(ctx["coexistence"]["forbidden_behaviors"])
    assert "AuthZ" in forbidden or "autorização" in forbidden


def test_stable_instructions_carry_fictional_identity() -> None:
    """Actions-side persona channel: the Builder Instructions paste covers
    who VISTA is, the fictional DAVI relationship and its boundaries."""
    doc = (
        API_DIR / "docs" / "gpt-actions" / "specialist-instructions.md"
    ).read_text(encoding="utf-8")
    heading = "## Instructions (colar no GPT Builder)"
    start = doc.index("```text\n", doc.index(heading)) + len("```text\n")
    block = doc[start:doc.index("\n```", start)]
    for marker in ("VISTA", "20 anos", "óculos", "DAVI", "fictícia",
                   "tool real"):
        assert marker in block, marker
