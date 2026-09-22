"""Evals / drift gates for VISTA specialist Instructions + Knowledge."""

from __future__ import annotations

from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "gpt-actions" / "specialist-instructions.md"
PLAYBOOKS = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "gpt-actions"
    / "vista-display-playbooks.md"
)
BUILDER_HARD_LIMIT = 8000
PROJECT_TARGET_LIMIT = 7000

EXPECTED_OPS = (
    "gpt_get_catalog",
    "gpt_list_playlists",
    "gpt_get_playlist_context",
    "gpt_search_data_routes",
    "gpt_preview_data_block",
    "gpt_suggest_change",
    "gpt_preview_change",
    "gpt_commit_change",
)


def _builder_instructions_block() -> str:
    text = DOC.read_text(encoding="utf-8")
    heading = "## Instructions (colar no GPT Builder)"
    start = text.index("```text\n", text.index(heading)) + len("```text\n")
    end = text.index("\n```", start)
    return text[start:end]


def test_vista_builder_instructions_fit_character_budget():
    block = _builder_instructions_block()
    assert len(block) <= PROJECT_TARGET_LIMIT, len(block)
    assert len(block) < BUILDER_HARD_LIMIT


def test_vista_identity_and_acronym_documented():
    text = DOC.read_text(encoding="utf-8")
    assert "VISTA — Especialista em Painéis Operacionais DELPI" in text
    assert "Visualização" in text and "Inteligência" in text and "Síntese" in text
    assert "Telas" in text and "Apresentação" in text


def test_vista_builder_core_keeps_required_invariants():
    block = _builder_instructions_block()
    required = [
        "INFERRED != FACT",
        "PROPOSED != SAVED",
        "PREVIEW != PERSISTED",
        "TECHNICAL SUCCESS != VERIFIED BUSINESS OUTCOME",
        "Search miss != proof of absence",
        "VISTA capability <= capability do usuário autenticado",
        "commit_now=true",
        "vista-display-playbooks.md",
        "gpt_get_catalog",
        "gpt_commit_change",
        "confirmation != authorization",
        "2xx != verified",
        "401=AuthN",
        "403=AuthZ",
        "proposal_handle",
        "latest",
    ]
    for marker in required:
        assert marker in block, marker


def test_vista_modes_are_present():
    block = _builder_instructions_block()
    for mode in (
        "QUICK DISPLAY",
        "GUIDED DASHBOARD",
        "DATA INTERPRETATION",
        "PLAYLIST CURATION",
    ):
        assert mode in block, mode


def test_vista_user_facing_language_is_portuguese_first():
    block = _builder_instructions_block()
    for marker in [
        "## Linguagem com o usuário",
        "português claro",
        "OBSERVED/INFORMED → Informado/Observado",
        "INFERRED → Hipótese",
        "PROPOSED → Proposto",
        "UNKNOWN → Ainda não sabemos",
        "Não altere nomes técnicos ao chamar Actions",
    ]:
        assert marker in block, marker


def test_vista_authority_and_no_second_truth():
    block = _builder_instructions_block()
    assert "NÃO é fonte de verdade" in block or "nao e fonte" in block.lower()
    assert "Knowledge nunca substitui dado vivo" in block
    assert "Core = RBAC" in block or "Core = RBAC de plataforma" in block
    assert "Sem SQL" in block or "sem SQL" in block.lower()


def test_vista_live_discovery_uses_official_actions_only():
    block = _builder_instructions_block()
    assert "gpt_search_data_routes" in block
    assert "gpt_preview_data_block" in block
    assert "Nunca invente operationId" in block
    for op in EXPECTED_OPS:
        assert op in DOC.read_text(encoding="utf-8"), op


def test_vista_prepare_act_states_are_distinct():
    block = _builder_instructions_block()
    for marker in [
        "VALIDATED",
        "CONFIRMED",
        "COMMIT_ATTEMPTED",
        "PERSISTED",
        "VERIFIED",
        "commit attempted != persisted",
        "PREVIEW != PERSISTED",
        "NÃO pergunte “Confirma?”",
        "commit_now",
    ]:
        assert marker in block, marker


def test_vista_playbooks_exist_and_forbid_new_actions_by_default():
    text = PLAYBOOKS.read_text(encoding="utf-8")
    assert "Mode Router" in text
    assert "Live data discovery" in text
    assert "No new GPT Actions without architecture evidence" in text
    assert "Knowledge **never** replaces live data" in text or "never** replaces live data" in text
    assert "INFERRED != FACT" in text
    assert "Intent Resolution / Desired Outcome" in text
    assert "CURRENT LIMITATION (PROVEN)" not in text or "PlanCompiler" in text
    assert "PlanCompiler" in text or "synthetic" in text.lower()
    assert "Never infer a UUID from a screenshot" in text
    assert "ninth Action" in text
    assert "commit_now" in text


def test_vista_instructions_domain_intent_beats_image_generation():
    block = _builder_instructions_block()
    assert "## Intenção de domínio" in block
    assert "NÃO tratar automaticamente como geração de imagem" in block
    assert "## Resultado desejado" in block
    assert "## Pedido composto" in block
    assert "LOTE COMPLETO" in block
    assert "PlanCompiler" in block
    assert "Pule gpt_suggest_change" in block
    assert "commit_now=true" in block
