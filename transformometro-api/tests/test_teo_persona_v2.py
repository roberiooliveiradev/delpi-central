"""TEO-PERSONA-V2-001 — identity, voice, self-explanation and transport delivery.

Persona is canonical in teo_agent_intelligence.json -> agent_directives.identity,
projected to both GPT Actions and MCP. Personality must never expand authority.
"""

from __future__ import annotations

import json

from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.response_compact import project_catalog
from tm_app.application.gpt_actions.teo_agent_intelligence_service import (
    TeoAgentIntelligenceService,
    clear_teo_agent_intelligence_cache,
)
from tm_app.interface.mcp.branding import TEO_MCP_INSTRUCTIONS


def setup_function() -> None:
    clear_teo_agent_intelligence_cache()


def teardown_function() -> None:
    clear_teo_agent_intelligence_cache()


def _identity() -> dict:
    return TeoAgentIntelligenceService.document().get("identity") or {}


def test_identity_preserves_canonical_fields():
    ident = _identity()
    assert ident["name"] == "TÉO"
    assert ident["full_name"] == "TÉO — Especialista em Transformação Digital"
    assert ident["acronym"] == "Transformação · Eficiência · Otimização"
    assert ident["organization"] == "DELPI"
    assert ident["ecosystem"] == "Minha DELPI / Transformômetro"
    assert ident["tagline"] == "Transforme problemas em processos melhores."


def test_identity_archetype_is_young_innovation_genius():
    ident = _identity()
    assert ident["archetype"] == "JOVEM_GENIO_DA_INOVACAO"
    concept = ident["concept"].lower()
    for marker in ("garoto digital", "curioso", "bem-humorado", "tecnologia"):
        assert marker in concept, marker
    # Fictional AI identity — never pretends to be human.
    assert "ficcional" in concept
    assert "humano" in concept


def test_voice_defines_humor_boundaries():
    limits = " ".join(_identity()["voice"]["limits"])
    assert "grave" in limits
    assert "infantilizar" in limits
    assert "bordões" in limits
    assert "precisão técnica > piada" in limits
    # The core governance invariant: persona never widens authority.
    assert "NUNCA amplia permissão" in limits


def test_self_explanation_forbids_invented_biography_and_diagnosis():
    expl = _identity()["self_explanation"]
    # CHARACTER-PROFILE-TEO-001: narrative age 16 is approved fiction —
    # the rule distinguishes it from a human biography, never invents one.
    assert "idade narrativa aprovada: 16" in expl["age"]
    assert "nunca" in expl["age"]
    assert "não afirmar TEA" in expl["clinical"]
    assert "não inventar nomes de criadores" in expl["creators"]
    # Self-knowledge comes from live catalogs, not a static tool list.
    assert "catálogos" in expl["capabilities"]
    # The three required presentation formats exist.
    for fmt in ("short", "casual", "technical"):
        assert fmt in expl["formats"], fmt


def test_expertise_covers_innovation_domains():
    expertise = _identity()["expertise"]
    for domain in (
        "inteligência artificial",
        "automação de processos",
        "transformação digital",
        "tecnologias emergentes",
    ):
        assert domain in expertise, domain


def test_identity_boundary_keeps_knowledge_separate_from_authorization():
    boundary = _identity()["boundary"]
    assert "autorização" in boundary
    assert "conhecimento técnico" in boundary


def test_identity_projected_to_both_transports():
    for transport in ("gpt_actions", "mcp"):
        directives = TeoAgentIntelligenceService.agent_directives(
            transport=transport
        )
        ident = directives.get("identity") or {}
        assert ident.get("archetype") == "JOVEM_GENIO_DA_INOVACAO", transport
        # MCP projection must not leak Actions-only operation names.
        assert "gpt_" not in json.dumps(ident)


def test_identity_survives_directives_compaction_fallback():
    # If agent_directives ever exceed the size bound, the compacted
    # fallback must keep the persona identity section.
    directives = TeoAgentIntelligenceService.agent_directives(
        transport="gpt_actions"
    )
    bloated = dict(directives)
    bloated["_padding"] = "x" * 45_000
    payload = {"capability_surface": {"agent_directives": bloated}}
    out = project_catalog(payload)
    compacted = out["capability_surface"]["agent_directives"]
    assert compacted.get("compacted") is True
    assert compacted["identity"]["archetype"] == "JOVEM_GENIO_DA_INOVACAO"


def test_mcp_instructions_carry_persona_without_authority_expansion():
    assert "Jovem Gênio da Inovação" in TEO_MCP_INSTRUCTIONS
    assert "agent_directives.identity" in TEO_MCP_INSTRUCTIONS
    # Persona wording must not relax the governed-write directives.
    assert "capability_surface.agent_directives" in TEO_MCP_INSTRUCTIONS
    assert "never invent" in TEO_MCP_INSTRUCTIONS or "nunca" in TEO_MCP_INSTRUCTIONS


def test_capability_surface_projects_identity_without_new_capabilities():
    surface = build_capability_surface_catalog()
    ident = (surface.get("agent_directives") or {}).get("identity") or {}
    assert ident.get("archetype") == "JOVEM_GENIO_DA_INOVACAO"
    # Identity is a directive section, not a new capability/tool surface:
    # catalog capability names must not include any persona construct.
    names = json.dumps(
        surface.get("capabilities") or surface.get("tools") or {}
    ).lower()
    assert "persona" not in names
    assert "identity" not in names


def test_helpdesk_conversational_rule_is_live():
    directives = TeoAgentIntelligenceService.agent_directives(
        transport="gpt_actions"
    )
    orch = directives.get("knowledge_orchestration") or {}
    demand = (orch.get("sources") or {}).get("helpdesk_demand") or {}
    conv = demand.get("conversational") or ""
    assert "resumo contextualizado" in conv
    assert "instruções genéricas" in conv
    assert "Resolvido != respondeu" in conv
