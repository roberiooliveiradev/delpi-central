"""R01/R10 — Agent investigation instructions must stay owner-agnostic.

Provider-/tool-specific workflows belong in live tools/list contracts,
never in the general Agent system instructions. Schema-derived hints
appended per tool from published inputSchema remain legitimate.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _EnvelopeHintedToolset,
    _INVESTIGATION_INSTRUCTION_VERSION,
    _INVESTIGATION_INSTRUCTIONS,
)


_PROVIDER_SPECIFIC_PATTERNS = (
    re.compile(r"\bdavi\.[a-z0-9_.]+\b", re.I),
    re.compile(r"\bteo\.[a-z0-9_.]+\b", re.I),
    re.compile(r"\bvista\.[a-z0-9_.]+\b", re.I),
    re.compile(r"\bexecute_delpi_information\b", re.I),
    re.compile(r"\bdiscover_delpi_information\b", re.I),
    re.compile(r"\bdiscover_\*", re.I),
    re.compile(r"\b\*_discover\*\b", re.I),
)

# Universal "every MCP needs candidate_token / discover→execute"
# workflows are forbidden in general instructions. Schema-local
# mentions inside _EnvelopeHintedToolset remain allowed.
_UNIVERSAL_ENVELOPE_COUPLING = re.compile(
    r"When a tool's schema declares\s+``candidate_token``|"
    r"you MUST first call the sibling discovery tool|"
    r"Concrete\s+example:\s+for\s+\"product",
    re.I,
)


def test_r01_investigation_instructions_are_provider_agnostic() -> None:
    text = _INVESTIGATION_INSTRUCTIONS
    assert _INVESTIGATION_INSTRUCTION_VERSION.startswith("generalist")
    hits: list[str] = []
    for pattern in _PROVIDER_SPECIFIC_PATTERNS:
        found = pattern.findall(text)
        hits.extend(found)
    assert hits == [], f"provider-specific instruction leakage: {hits}"
    assert _UNIVERSAL_ENVELOPE_COUPLING.search(text) is None


def test_r10_removed_legacy_tool_names_not_required_by_instructions() -> None:
    """A retired owner tool name must not be demanded by Agent rules."""
    obsolete = (
        "davi.execute_delpi_information",
        "execute_delpi_information",
        "discover_delpi_information",
        "discover_*",
    )
    lowered = _INVESTIGATION_INSTRUCTIONS.casefold()
    for name in obsolete:
        assert name.casefold() not in lowered


def test_instruction_source_is_governed_resource_not_inline_prose() -> None:
    """Load path: investigation_instructions.delpi.json → select → Agent."""
    module_path = (
        Path(__file__).resolve().parents[1]
        / "app/infrastructure/orchestration/pydantic_ai_investigation.py"
    )
    source = module_path.read_text(encoding="utf-8")
    assert "load_selected_investigation_instructions" in source
    assert "investigation_instructions.delpi.json" in source
    assert "You are DÉLIA's generalist semantic investigation agent" not in source
    resource = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "investigation_instructions.delpi.json"
    )
    assert resource.is_file()
    # Compatibility exports remain for harnesses/tests.
    assert _INVESTIGATION_INSTRUCTION_VERSION.startswith("generalist")
    assert _INVESTIGATION_INSTRUCTIONS.strip()


def test_envelope_hint_is_schema_derived_not_owner_hardcoded() -> None:
    """candidate_token guidance appears only when the live schema declares it."""
    from dataclasses import dataclass

    @dataclass
    class _FakeDef:
        description: str
        parameters_json_schema: dict

    @dataclass
    class _FakeTool:
        tool_def: _FakeDef

    class _FakeWrapped:
        async def get_tools(self, ctx):
            return {
                "owner.read": _FakeTool(
                    _FakeDef(
                        "Read data",
                        {
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "arguments": {"type": "object"},
                            },
                        },
                    )
                ),
                "owner.execute": _FakeTool(
                    _FakeDef(
                        "Execute candidate",
                        {
                            "type": "object",
                            "properties": {
                                "candidate_token": {"type": "string"},
                                "arguments": {"type": "object"},
                            },
                        },
                    )
                ),
            }

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    hinted = _EnvelopeHintedToolset(_FakeWrapped())
    tools = asyncio.run(hinted.get_tools(None))
    read_desc = tools["owner.read"].tool_def.description
    exec_desc = tools["owner.execute"].tool_def.description
    assert "candidate_token" not in read_desc
    assert "candidate_token" in exec_desc
    assert "JSON objects" in exec_desc or "object" in exec_desc.lower()
