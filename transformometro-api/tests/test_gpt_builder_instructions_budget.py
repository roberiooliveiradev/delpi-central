from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "gpt-actions" / "specialist-instructions.md"
BUILDER_HARD_LIMIT = 8000
PROJECT_TARGET_LIMIT = 3500


def _builder_instructions_block() -> str:
    text = DOC.read_text(encoding="utf-8")
    heading = "## Instructions (colar no GPT Builder)"
    start = text.index("```text\n", text.index(heading)) + len("```text\n")
    end = text.index("\n```", start)
    return text[start:end]


def test_teo_builder_instructions_fit_character_budget():
    block = _builder_instructions_block()
    assert len(block) <= PROJECT_TARGET_LIMIT
    assert len(block) < BUILDER_HARD_LIMIT


def test_teo_builder_core_keeps_required_invariants():
    block = _builder_instructions_block()
    required = [
        "agent_directives",
        "INFERRED != FACT",
        "Search miss != proof of absence",
        "TÉO capability <= authenticated user capability",
        "PREPARE EXACT CHANGE",
        "EXPLICIT CONFIRMATION",
        "AUTHORITATIVE READ-BACK",
        "commit_now",
        "meeting_minute",
        "teo-method-playbooks.md",
        "OUTCOME_VERIFICATION_FAILED",
    ]
    for marker in required:
        assert marker in block, marker


def test_teo_builder_obeys_live_directives_not_universal_confirm_on_additive():
    block = _builder_instructions_block()
    assert "agent_directives" in block
    assert "commit_now=true" in block or "commit_now" in block
    # Additive must not force Confirma? — destructive still has EXPLICIT CONFIRMATION
    assert "NÃO perguntar Confirma?" in block or "não perguntar Confirma?" in block.lower()


def test_teo_builder_user_facing_language_is_portuguese_first():
    block = _builder_instructions_block()
    required = [
        "## Linguagem com o usuário",
        "português claro",
        "INFERRED → Hipótese",
        "PROPOSED → Proposto",
        "UNKNOWN → Ainda não sabemos",
        "AS-IS → processo atual",
        "TO-BE → processo futuro proposto",
        "Não altere nomes técnicos ao chamar Actions",
    ]
    for marker in required:
        assert marker in block, marker


def test_teo_builder_does_not_leak_full_flow_pipelines():
    block = _builder_instructions_block()
    assert "GUIDED TRANSFORMATION\nUNDERSTAND PROBLEM" not in block
    assert "progressive: USER PROBLEM → 2–5 conceitos" not in block
