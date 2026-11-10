"""G04/G05/G11 — orchestration must not depend on fixed MCP tool names.

These harnesses prove the Agent instruction surface stays usable when
owners rename tools or use top-level vs nested argument shapes. They do
not call live LLMs; they assert the contracts the Agent receives.
"""

from __future__ import annotations

from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _INVESTIGATION_INSTRUCTIONS,
)


def test_g04_g11_instructions_do_not_encode_fixed_tool_names() -> None:
    text = _INVESTIGATION_INSTRUCTIONS.casefold()
    for forbidden in (
        "get_context",
        "get_product_structure",
        "execute_delpi",
        "discover_delpi",
        "candidate_token",
        "arguments.query",
    ):
        assert forbidden not in text, forbidden


def test_g05_instructions_do_not_require_universal_arguments_envelope() -> None:
    text = _INVESTIGATION_INSTRUCTIONS
    assert "arguments must ALWAYS be a non-empty object" not in text
    assert "business identifiers never belong at the top level" not in text
    assert "schema declares" in text.casefold() or "tool schema" in text.casefold()


def test_g12_schema_guidance_defers_to_live_contract() -> None:
    text = " ".join(_INVESTIGATION_INSTRUCTIONS.casefold().split())
    assert "live tool surface" in text or "tool's description/schema" in text
    assert "as that schema declares" in text
