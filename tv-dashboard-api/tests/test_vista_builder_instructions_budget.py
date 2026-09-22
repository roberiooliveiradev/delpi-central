"""Evals / drift gates for VISTA specialist Instructions + deployable intelligence."""

from __future__ import annotations

from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "gpt-actions" / "specialist-instructions.md"
PLAYBOOKS = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "gpt-actions"
    / "vista-display-playbooks.md"
)
INTELLIGENCE = (
    Path(__file__).resolve().parents[1]
    / "tv_app"
    / "content"
    / "vista_agent_intelligence.json"
)
BUILDER_HARD_LIMIT = 8000
# Stable Instructions only — mutable behavior lives in agent_directives.
PROJECT_TARGET_LIMIT = 3500

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
        "agent_directives",
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


def test_vista_instructions_delegate_mutable_behavior_to_catalog():
    block = _builder_instructions_block()
    assert "capability_surface.agent_directives" in block
    assert "por completo" in block
    # Section names / heuristics must NOT live in Builder paste.
    assert "object_resolution" not in block
    assert "screenshot_parity" not in block
    assert "QUICK DISPLAY" not in block
    assert "ALTER_EXISTING_BEFORE_CREATE" not in block
    assert "PRINT_TO_TYPED_SLIDE_PARITY" not in block


def test_builder_instructions_must_not_leak_intelligence_json_keys():
    """Regression gate: feature heuristics stay in deployable JSON, not Builder paste."""
    import json

    intelligence = json.loads(INTELLIGENCE.read_text(encoding="utf-8"))
    block = _builder_instructions_block()
    # Top-level behavioral sections (except metadata).
    forbidden_keys = {
        key
        for key in intelligence.keys()
        if key
        not in {
            "version",
            "owner",
            "source",
            "auth_errors",  # codes may be paraphrased; still prefer catalog
        }
    }
    for key in sorted(forbidden_keys):
        assert key not in block, f"Instructions leaked intelligence key: {key}"

    # Explicit principles / mode ids from nested structures.
    forbidden_tokens: list[str] = []
    resolution = intelligence.get("object_resolution") or {}
    if isinstance(resolution, dict) and resolution.get("principle"):
        forbidden_tokens.append(str(resolution["principle"]))
    parity = intelligence.get("screenshot_parity") or {}
    if isinstance(parity, dict) and parity.get("principle"):
        forbidden_tokens.append(str(parity["principle"]))
    modes = intelligence.get("modes") or {}
    if isinstance(modes, dict):
        forbidden_tokens.extend(str(name) for name in modes.keys())
    for token in forbidden_tokens:
        assert token not in block, f"Instructions leaked intelligence token: {token}"


def test_specialist_doc_documents_forbidden_instructions_gate():
    text = DOC.read_text(encoding="utf-8")
    assert "PROIBIDO no bloco Instructions" in text
    assert "vista_agent_intelligence.json" in text
    assert "test_vista_builder_instructions_budget.py" in text


def test_vista_instructions_domain_intent_beats_image_generation():
    block = _builder_instructions_block()
    assert "Image Generation" in block
    assert "arte/imagem externa" in block or "arte/imagem" in block
    assert "agent_directives" in block


def test_vista_user_facing_language_is_portuguese_first():
    block = _builder_instructions_block()
    for marker in [
        "Português claro",
        "Nunca invente",
        "Actions",
    ]:
        assert marker in block, marker


def test_vista_authority_and_no_second_truth():
    block = _builder_instructions_block()
    assert "NÃO é fonte de verdade" in block or "nao e fonte" in block.lower()
    assert "Knowledge nunca substitui" in block
    assert "sem sql" in block.lower()


def test_vista_live_discovery_ops_documented_in_doc():
    text = DOC.read_text(encoding="utf-8")
    for op in EXPECTED_OPS:
        assert op in text, op


def test_vista_prepare_act_skeleton_in_instructions():
    block = _builder_instructions_block()
    for marker in [
        "commit_now=true",
        "proposal_handle",
        "VERIFIED",
        "persisted=true",
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
    assert "VISUAL_PARITY" in text or "screenshot_parity" in text
    assert "ninth Action" in text
    assert "commit_now" in text
