"""CHARACTER-PROFILE-CLARA-001 — CLARA ficha via delpi_character_profiles.

Shared owns the structure; controllership-finance-api owns the CLARA
profile. Fiction only: the ficha never grants tools, permissions or
authority (doc 94 — identidade aprovada pelo PO).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from delpi_character_profiles import (
    FICTION_IDENTITY_ONLY,
    profile_from_dict,
    profile_to_dict,
    project_persona_context,
    public_profile_from_dict,
    public_profile_to_dict,
    validate_profile,
    validate_relationship_consistency,
)

from controllership_finance_app.application.clara.agent_intelligence_service import (  # noqa: E501
    ClaraAgentIntelligenceService,
)
from controllership_finance_app.persona.clara_profile import (
    build_clara_profile,
    get_clara_profile,
)

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parent

AVATAR_REF = "controllership_finance_app/assets/characters/clara/avatar-v1.jpg"
AVATAR_PATH = APP_ROOT / AVATAR_REF
AVATAR_SHA256 = (
    "967e79b8086673f34b52e574330e7d94669728cfe60269005e754c3fc49f140f"
)


def _profile():
    return get_clara_profile()


def _jpeg_size(raw: bytes) -> tuple[int, int]:
    """Stdlib-only JPEG SOF parser — returns (width, height)."""
    assert raw[:2] == b"\xff\xd8"
    i = 2
    while i < len(raw):
        if raw[i] != 0xFF:
            i += 1
            continue
        marker = raw[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height = int.from_bytes(raw[i + 5:i + 7], "big")
            width = int.from_bytes(raw[i + 7:i + 9], "big")
            return width, height
        seg_len = int.from_bytes(raw[i + 2:i + 4], "big")
        i += 2 + seg_len
    raise AssertionError("no SOF marker found")


def test_profile_builds_and_validates_without_errors():
    issues = validate_profile(_profile())
    errors = [i for i in issues if i.severity == "ERROR"]
    assert errors == []
    # No warnings are accepted silently — keep this strict.
    assert [i for i in issues if i.severity == "WARNING"] == []


def test_shared_contract_import_and_profile_instantiation():
    p = _profile()
    assert p.identity.character_id == "clara"
    assert p.profile_version == 1
    assert p.narrative_classification == FICTION_IDENTITY_ONLY
    rebuilt = profile_from_dict(profile_to_dict(p))
    assert rebuilt == p


def test_identity_fields():
    ident = _profile().identity
    assert ident.character_id == "clara"
    assert ident.name == "CLARA"
    assert ident.display_name == (
        "CLARA — Especialista em Controladoria & Finanças"
    )
    assert ident.title == "Especialista em Controladoria & Finanças"
    assert ident.organization == "Minha DELPI"
    assert ident.narrative_age == "34 anos"
    assert ident.gender_identity == "feminina"
    assert ident.pronouns == "ela/dela"
    assert "Controladoria" in ident.short_introduction


def test_appearance_reflects_official_avatar():
    app = _profile().appearance
    assert app.avatar_status == "OFFICIAL_AVATAR_APPROVED"
    assert app.avatar_reference == AVATAR_REF
    assert "ruiv" in app.hair
    assert "castanhos" in app.eyes
    assert "azul-marinho" in app.clothing
    assert "3D" in app.visual_style


def test_official_avatar_asset_stored_with_stable_reference():
    ref = _profile().appearance.avatar_reference
    assert ref == AVATAR_REF
    assert not ref.startswith("/mnt/data")
    assert AVATAR_PATH.is_file()
    raw = AVATAR_PATH.read_bytes()
    # JPEG magic bytes + pinned approved content.
    assert raw[:3] == b"\xff\xd8\xff"
    assert hashlib.sha256(raw).hexdigest() == AVATAR_SHA256
    # Approved composition is square 1:1 bust framing.
    width, height = _jpeg_size(raw)
    assert (width, height) == (1024, 1024)
    assert width == height


def test_personality_traits_and_humor_bounds():
    p = _profile().personality
    traits = " ".join(p.core_traits).lower()
    for marker in ("serena", "analítica", "organizada", "empática"):
        assert marker in traits, marker
    assert "nunca" in p.humor_style
    assert "equilibrado" in p.temperament


def test_communication_style():
    c = _profile().communication
    assert c.language == "pt-BR"
    assert c.formality == "moderada"
    assert c.preferred_expressions  # voice examples, non-mandatory
    assert any("fonte" in e for e in c.preferred_expressions)


def test_expertise_is_narrative_not_tools():
    e = _profile().expertise
    assert e.specialties
    blob = " ".join(e.specialties + e.knowledge_domains).lower()
    for forbidden in (
        "tool", "permission", "credential", "endpoint", "gpt_",
    ):
        assert forbidden not in blob, forbidden
    assert "controladoria" in blob


def test_story_and_approved_events():
    s = _profile().story
    assert "fictício" in s.origin_story
    assert s.personal_mission
    assert s.current_story_arc
    ids = {e.event_id for e in s.events}
    assert ids == {
        "clara-origin",
        "clara-analytical-path",
        "clara-joins-minha-delpi",
        "clara-controllership-arc",
    }
    # No invented real dates on narrative events.
    assert all(not e.narrative_date for e in s.events)
    # No invented encounters: events are CLARA-only.
    assert all(e.participants == ("clara",) for e in s.events)


def test_relationships_are_public_colleagues():
    rels = {r.target_character_id: r for r in _profile().relationships}
    assert set(rels) == {"davi", "vista", "teo"}
    for r in rels.values():
        assert r.relationship_type == "colleagues"
        assert r.visibility == "public"
    # CLARA has no romantic/family relationships — none approved.
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
    assert "culpa" in conduct.error_communication


def test_narrative_classification_is_fiction_only():
    assert _profile().narrative_classification == "FICTION_IDENTITY_ONLY"
    assert _profile().universe.startswith("Especialistas DELPI")


def test_persona_context_projection():
    ctx = project_persona_context(_profile())
    json.dumps(ctx, ensure_ascii=False)
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    assert ctx["identity"]["character_id"] == "clara"
    assert ctx["identity"]["narrative_age"] == "34 anos"
    assert ctx["avatar_status"] == "OFFICIAL_AVATAR_APPROVED"
    assert ctx["avatar_reference"] == AVATAR_REF
    assert ctx["appearance_summary"]
    assert ctx["personality_summary"]
    rel_ids = {r["target_character_id"] for r in ctx["relationships"]}
    assert rel_ids == {"davi", "vista", "teo"}
    # Full story/events stay out of the bounded context payload.
    assert "events" not in json.dumps(ctx)
    # Bounded context payload.
    size = len(json.dumps(ctx, ensure_ascii=True).encode("utf-8"))
    assert size < 8_000


def test_public_profile_excludes_internals_and_operational_data():
    pub = ClaraAgentIntelligenceService.public_profile()
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
    assert payload["character_id"] == "clara"
    assert payload["public_projection_version"] >= 1
    # Committed artifact matches the live projection.
    artifact = json.loads(
        (
            APP_ROOT
            / "controllership_finance_app"
            / "content"
            / "clara_public_profile.json"
        ).read_text(encoding="utf-8")
    )
    assert artifact == payload


def test_public_projection_roundtrip_serialization():
    pub = ClaraAgentIntelligenceService.public_profile()
    restored = public_profile_from_dict(public_profile_to_dict(pub))
    assert restored.character_id == "clara"
    assert restored.relationships == pub.relationships


def _load_public_artifact(relative: str):
    path = REPO_ROOT / relative
    if not path.exists():
        return None
    return public_profile_from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def test_relationship_consistency_with_published_profiles():
    """Cross-check against committed public profiles (DAVI/VISTA/TÉO).

    ``colleagues`` expects a reciprocal edge; the colleague fichas predate
    CLARA and do not declare one — the contract reports WARNING, never
    ERROR. Warnings are documented (handoffs); only contradictions fail.
    """
    profiles = [ClaraAgentIntelligenceService.public_profile()]
    for rel in (
        "api-delpi/app/content/davi_public_profile.json",
        "tv-dashboard-api/tv_app/content/vista_public_profile.json",
        "transformometro-api/tm_app/content/teo_public_profile.json",
    ):
        loaded = _load_public_artifact(rel)
        if loaded is not None:
            profiles.append(loaded)
    issues = validate_relationship_consistency(profiles)
    assert [i for i in issues if i.severity == "ERROR"] == []
    # DAVI–VISTA romantic relationship is preserved on both sides.
    by_id = {
        p.character_id: p for p in profiles if p.character_id != "clara"
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


def test_agent_directives_integrate_character_on_mcp():
    directives = ClaraAgentIntelligenceService.agent_directives()
    ch = directives.get("character") or {}
    assert ch["identity"]["character_id"] == "clara"
    assert ch["identity"]["narrative_age"] == "34 anos"
    assert ch["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    # Operational directives preserved — narrative never replaces them.
    for key in ("read_first", "citations", "confirmation"):
        assert directives.get(key), key


def test_character_never_appears_as_capability_or_tool():
    from controllership_finance_app.interface.mcp.constants import (
        MCP_TOOL_NAMES,
    )

    # Narrative is not a tool: frozen surface stays at the declared
    # set (6 tools semânticas estáveis — CLARA-MCP-SEMANTIC-001).
    assert len(MCP_TOOL_NAMES) == 6
    for name in MCP_TOOL_NAMES:
        for forbidden in ("persona", "character", "story", "narrative"):
            assert forbidden not in name.lower()


def test_ficha_is_local_to_controllership_finance_not_shared():
    import delpi_character_profiles

    pkg = Path(delpi_character_profiles.__file__).parent
    for py in pkg.rglob("*.py"):
        assert "clara_profile" not in py.name
        text = py.read_text("utf-8").lower()
        assert 'character_id="clara"' not in text


def test_context_covers_identity_questions():
    """'quem é você?', 'quantos anos?', 'quem são seus colegas?' — the
    compact context carries everything a host needs."""
    ctx = ClaraAgentIntelligenceService.persona_context()
    assert "CLARA" in ctx["identity"]["name"]
    assert "Controladoria" in ctx["identity"]["role"]
    assert "34" in ctx["identity"]["narrative_age"]
    assert "ruiv" in ctx["appearance_summary"]
    davi = [
        r
        for r in ctx["relationships"]
        if r["target_character_id"] == "davi"
    ]
    assert davi and "DAVI" in davi[0]["description"]


def test_context_distinguishes_fiction_from_operations():
    ctx = ClaraAgentIntelligenceService.persona_context()
    assert ctx["narrative_classification"] == "FICTION_IDENTITY_ONLY"
    rules = " ".join(
        ctx["coexistence"]["forbidden_behaviors"]
    )
    assert "governados" in rules  # ACT only via governed contracts


def test_build_from_explicit_doc_roundtrip():
    p = build_clara_profile()
    assert p.identity.character_id == "clara"
    assert validate_profile(p) == []
