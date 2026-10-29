"""DAVI-INTELLIGENCE-002 — specialist persona, knowledge and context delivery.

Covers the bounded additions: canonical persona contract, specialist
directives projected through capability_surface.agent_directives, MCP
server-instruction persona echo, Agent Studio paste parity and the
material-movement retrieval aliases. No new tools, ops or AuthZ.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.external_capabilities.davi_agent_intelligence_service import (
    DAVI_AGENT_DIRECTIVES_MAX_BYTES,
    DaviAgentIntelligenceService,
    clear_davi_agent_intelligence_cache,
)
from app.interface.mcp.branding import DAVI_MCP_INSTRUCTIONS


@pytest.fixture(autouse=True)
def _clear_caches():
    clear_davi_agent_intelligence_cache()
    yield
    clear_davi_agent_intelligence_cache()


# ---------------------------------------------------------------------------
# Grupo A — persona (canonical source + surfaces)
# ---------------------------------------------------------------------------


def test_persona_section_is_governed_and_projected() -> None:
    doc = DaviAgentIntelligenceService.document()
    persona = doc.get("persona") or {}
    assert "garoto" in persona["identity"]
    for trait in ("curioso", "inteligente", "bem-humorado", "travesso"):
        assert trait in persona["identity"], trait
    assert "especialista em dados" in persona["identity"]
    # Answer-first and bounded suggestions are contractual behavior.
    blob = json.dumps(persona, ensure_ascii=False)
    assert "Atender primeiro" in blob
    assert "capabilities autorizadas" in blob
    # Projected to dynamic surface so plugin chats receive the tone echo.
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["persona"]["identity"] == persona["identity"]


def test_persona_bridge_declares_stable_surfaces_and_no_authority() -> None:
    bridge = DaviAgentIntelligenceService.agent_directives()["persona_bridge"]
    assert "Agent Studio" in bridge["stable_in"]
    assert "MCP server instructions" in bridge["stable_in"]
    assert "não concede permissão" in bridge["authority"]
    assert "agent_directives.persona" in bridge["runtime_echo"]


def test_mcp_instructions_carry_persona_without_mutable_keys() -> None:
    text = DAVI_MCP_INSTRUCTIONS
    # Persona echo in the stable MCP channel (initialize instructions).
    assert "curious" in text
    assert "good-humored" in text
    assert "mischievous" in text
    assert "male persona" in text
    assert "Answer the user's request first" in text
    assert "UX" in text and "never authority" in text
    # Metadata-first resolution guidance without naming operationIds.
    assert "metadata" in text.lower()
    assert "never invent table or column names" in text
    # Still no mutable principle codes or operationIds.
    assert "TRY_TOOL_BEFORE_CLAIMING_UNAVAILABLE" not in text
    assert "DISCOVER_THEN_EXECUTE" not in text
    for op_id in ("search_products", "execute_readonly_sql", "get_product_stock"):
        assert op_id not in text


def test_agent_studio_paste_matches_persona_contract() -> None:
    doc = Path(__file__).resolve().parents[1] / (
        "docs/integrations/openai-workspace-agent-davi.md"
    )
    text = doc.read_text(encoding="utf-8")
    marker = "## Agent instructions — canonical stable contract"
    paste = text.split(marker, 1)[1].split("```text", 1)[1].split("```", 1)[0]
    assert "garoto curioso" in paste
    assert "bem-humorado" in paste
    assert "travesso" in paste
    assert "especialista em dados" in paste
    # Humor bounded — never trivializes serious topics.
    assert "infantilizar" in paste
    # Proactive suggestions bounded to authorized capabilities.
    assert "aprofundamento" in paste
    assert "capabilities" in paste and "autorizadas" in paste
    # Metadata-first resolution guidance present.
    assert "metadados" in paste


# ---------------------------------------------------------------------------
# Grupo B — specialist knowledge projected in agent_directives
# ---------------------------------------------------------------------------


def test_data_specialist_reasoning_is_projected() -> None:
    spec = DaviAgentIntelligenceService.agent_directives()["data_specialist"]
    assert spec["principle"] == "MINIMAL_SUFFICIENT_GOVERNED_SOURCE"
    blob = json.dumps(spec, ensure_ascii=False)
    assert "capability semântica" in blob
    assert "granularidade" in blob
    assert "zero linhas" in blob
    assert "metadata" in blob


def test_protheus_conventions_are_governed_guidance() -> None:
    pro = DaviAgentIntelligenceService.agent_directives()["protheus"]
    blob = json.dumps(pro, ensure_ascii=False)
    assert "SX2" in blob and "SX3" in blob
    assert "D_E_L_E_T_" in blob
    assert "search_tables_by_description" in blob
    # Never fabricate physical names from suffixes.
    assert "nunca fabricar nome físico" in blob
    # Metadata is not row authorization.
    assert "não autoriza" in blob or "autorização" in blob


def test_tsql_practices_are_projected() -> None:
    tsql = DaviAgentIntelligenceService.agent_directives()["tsql"]
    blob = json.dumps(tsql, ensure_ascii=False)
    assert "SELECT *" in blob
    assert "TOP" in blob and "ORDER BY" in blob
    assert "zeros à esquerda" in blob
    assert "execute_readonly_sql" in blob
    assert "DML" in blob  # write verbs explicitly forbidden


def test_table_discovery_pipeline_is_projected() -> None:
    td = DaviAgentIntelligenceService.agent_directives()["table_discovery"]
    pipeline = " ".join(td["pipeline"])
    assert "search_tables_by_description" in pipeline
    assert "discover_delpi_information" in pipeline
    assert "não autoriza" in " ".join(td["rules"])


def test_proactive_rules_are_bounded() -> None:
    pro = DaviAgentIntelligenceService.agent_directives()["proactive"]
    blob = json.dumps(pro, ensure_ascii=False)
    assert "ANSWER_FIRST_THEN_SUGGEST" in blob
    assert "capabilities autorizadas" in blob
    assert "Não executar consultas extras" in blob


def test_directives_budget_after_specialist_additions() -> None:
    size = DaviAgentIntelligenceService.directives_serialized_size()
    assert size <= DAVI_AGENT_DIRECTIVES_MAX_BYTES, size
    assert DAVI_AGENT_DIRECTIVES_MAX_BYTES == 32 * 1024


# ---------------------------------------------------------------------------
# Grupo C — retrieval aliases for material movements (v30)
# ---------------------------------------------------------------------------


def _allowlist() -> dict:
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "app/content/davi_external_read_allowlist.json"
        ).read_text(encoding="utf-8")
    )


def test_movements_aliases_cover_business_phrases() -> None:
    allow = _allowlist()
    entry = next(
        o for o in allow["operations"]
        if o["operationId"] == "get_product_internal_movements"
    )
    aliases = entry["semanticAliases"]
    for phrase in (
        "movimentos de materiais",
        "entrada de materiais",
        "registros de entrada de materiais",
        "saída de materiais",
        "movimentação do produto",
    ):
        assert phrase in aliases, phrase


def test_sql_aliases_cover_aggregate_movement_scan() -> None:
    allow = _allowlist()
    entry = next(
        o for o in allow["operations"]
        if o["operationId"] == "execute_readonly_sql"
    )
    aliases = entry["semanticAliases"]
    for phrase in (
        "produtos com movimentação",
        "produtos que tiveram movimentação",
        "movimentação no período",
    ):
        assert phrase in aliases, phrase


# ---------------------------------------------------------------------------
# Safety — persona/specialist additions do not weaken boundaries
# ---------------------------------------------------------------------------


def test_specialist_additions_keep_read_only_authority() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["read_only"] is True
    assert "write_flow" not in directives
    authority = directives["authority"]
    assert "NOT AuthZ" in authority
    # New sections carry no permission language that elevates metadata/persona.
    for key in ("persona", "protheus", "table_discovery"):
        assert directives.get(key), key


# ---------------------------------------------------------------------------
# DAVI-PERSONA-003 — fictional universe narrative (DAVI × VISTA)
# ---------------------------------------------------------------------------


def test_narrative_section_is_versioned_and_projected() -> None:
    doc = DaviAgentIntelligenceService.document()
    narrative = doc.get("narrative") or {}
    assert narrative["narrative_version"] == 1
    assert narrative["type"] == "FICTION_IDENTITY_ONLY"
    assert "Especialistas DELPI" in narrative["universe"]
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["narrative"]["narrative_version"] == 1
    assert (
        directives["narrative"]["narrative_version"]
        == narrative["narrative_version"]
    )


def test_vista_relationship_description_is_consistent() -> None:
    rel = DaviAgentIntelligenceService.agent_directives()["narrative"][
        "relationship"
    ]
    assert "VISTA" in rel["character"]
    assert "namorad" in rel["status"].lower()
    profile = rel["vista_profile"]
    for trait in ("20 anos", "pele clara", "pretos", "óculos", "proativa"):
        assert trait in profile, trait
    assert "painéis" in rel["character"] or "painéis" in profile
    assert "Complementares" in rel["dynamic"] or "complementares" in rel[
        "dynamic"
    ]


def test_narrative_boundaries_prevent_authority_drift() -> None:
    narrative = DaviAgentIntelligenceService.agent_directives()["narrative"]
    blob = json.dumps(narrative, ensure_ascii=False)
    # Fiction never becomes authorization/integration.
    assert "autorização" in blob or "AuthZ" in blob
    assert "não alterar" in blob.lower() or "Não alterar" in blob
    assert "MCPs" in blob
    # Mention rules bound frequency and truth.
    rules = " ".join(narrative["mention_rules"])
    assert "ocasionalmente" in rules
    assert "nunca" in rules.lower()
    assert "tool real" in rules


def test_appearance_reference_is_not_official_avatar() -> None:
    persona = DaviAgentIntelligenceService.agent_directives()["persona"]
    appearance = persona["appearance"]
    assert appearance["status"] == "REFERENCE_NOT_OFFICIAL_AVATAR"
    for trait in ("jovem", "escuros", "azul"):
        assert trait in appearance["description"], trait
    assert "não se repete" in appearance["rule"]


def test_mcp_instructions_carry_vista_echo_bounded() -> None:
    text = DAVI_MCP_INSTRUCTIONS
    assert "VISTA" in text
    assert "fictional" in text
    assert "occasionally" in text
    # Explicitly bounded — fiction is not a tool, permission or integration.
    assert "never a tool call" in text
    assert "permission" in text
    assert "MCP integration" in text


def test_agent_studio_paste_contains_narrative_block() -> None:
    doc = Path(__file__).resolve().parents[1] / (
        "docs/integrations/openai-workspace-agent-davi.md"
    )
    text = doc.read_text(encoding="utf-8")
    marker = "## Agent instructions — canonical stable contract"
    paste = text.split(marker, 1)[1].split("```text", 1)[1].split("```", 1)[0]
    assert "universo fictício" in paste.lower()
    assert "VISTA" in paste
    assert "namorada" in paste
    assert "ocasionalmente" in paste
    assert "não é autorização" in paste or "não é autorização, tool call" in paste
    assert "avatar oficial" in paste


def test_vista_handoff_document_exists_and_is_complete() -> None:
    handoff = Path(__file__).resolve().parents[1] / (
        "docs/integrations/evidence/DAVI-PERSONA-003-VISTA-HANDOFF.md"
    )
    text = handoff.read_text(encoding="utf-8")
    for required in (
        "HANDOFF — DAVI → VISTA",
        "namorados",
        "narrative_version",
        "óculos",
        "Não modificar diretamente o runtime VISTA",
    ):
        assert required in text, required


def test_narrative_additions_keep_tools_and_authz_unchanged() -> None:
    directives = DaviAgentIntelligenceService.agent_directives()
    assert directives["read_only"] is True
    assert directives["surface_parity"]["mcp_tools"] == 2
    size = DaviAgentIntelligenceService.directives_serialized_size()
    assert size <= DAVI_AGENT_DIRECTIVES_MAX_BYTES, size
