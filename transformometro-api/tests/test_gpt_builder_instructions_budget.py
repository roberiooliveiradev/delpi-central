from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "gpt-actions" / "specialist-instructions.md"
BUILDER_HARD_LIMIT = 8000
PROJECT_TARGET_LIMIT = 7000


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
        "INFERRED != FACT",
        "Search miss != proof of absence",
        "AS_IS != CURRENT_COMPOSED != TO_BE",
        "TÉO capability <= authenticated user capability",
        "PREPARE EXACT CHANGE",
        "EXPLICIT CONFIRMATION",
        "AUTHORITATIVE READ-BACK",
        "surface_supports = suporte, não autorização",
        "OUTCOME_VERIFICATION_FAILED",
        "teo-method-playbooks.md",
    ]
    for marker in required:
        assert marker in block
