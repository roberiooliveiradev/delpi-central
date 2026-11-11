"""INT-1 — model-visible tool description parity + pagination projection.

RED/GREEN for defects proven from stab-v2-5b0e914eb9 (Documento 298):

1. ``_EnvelopeHintedToolset`` truncated published MCP descriptions to
   ``[:500]`` when appending schema-derived hints, destroying owner
   semantic discrimination (e.g. TEO ``read`` entity contract).
2. ``_attempt_projection`` surfaced ``result_truncated`` without the
   existing owner pagination envelope (``page`` / ``has_more``), so the
   Agent could not construct a legitimate next-page call.

No specialist hardcoding. Reuses ``extract_pagination_envelope``.
"""

from __future__ import annotations

import asyncio
import dataclasses

import pytest

from app.application.capability_provision.generic_evidence_renderer import (
    extract_pagination_envelope,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import LIMITATION_RESULT_TRUNCATED
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _EnvelopeHintedToolset,
    _attempt_projection,
)


@dataclasses.dataclass
class _FakeDef:
    description: str
    parameters_json_schema: dict


@dataclasses.dataclass
class _FakeTool:
    tool_def: _FakeDef


def test_envelope_hint_preserves_long_owner_tool_description():
    """Published MCP description must remain model-visible after hints."""
    marker = "OWNER_SEMANTIC_TAIL:decomposition_tree|process|revision"
    long_desc = (
        "Semantic read — never writes. entity + typed action + params. "
        + ("x" * 520)
        + " "
        + marker
    )
    assert len(long_desc) > 500

    class _Wrapped:
        async def get_tools(self, ctx):
            return {
                "teo.read": _FakeTool(
                    _FakeDef(
                        long_desc,
                        {
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "params": {"type": "object"},
                            },
                        },
                    )
                )
            }

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    tools = asyncio.run(_EnvelopeHintedToolset(_Wrapped()).get_tools(None))
    desc = tools["teo.read"].tool_def.description
    assert marker in desc, (
        "owner description tail was truncated away by envelope hints"
    )
    assert long_desc in desc or desc.startswith(
        long_desc[: len(long_desc) // 2]
    )
    # Schema-derived object hint still present (non-owner-specific).
    assert "JSON objects" in desc or "object" in desc.casefold()


def test_envelope_hint_preserves_short_description_and_adds_hint():
    class _Wrapped:
        async def get_tools(self, ctx):
            return {
                "davi.read": _FakeTool(
                    _FakeDef(
                        "Read DELPI business data through one governed capability.",
                        {
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "arguments": {"type": "object"},
                            },
                        },
                    )
                )
            }

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    tools = asyncio.run(_EnvelopeHintedToolset(_Wrapped()).get_tools(None))
    desc = tools["davi.read"].tool_def.description
    assert desc.startswith(
        "Read DELPI business data through one governed capability."
    )
    assert "arguments object" in desc.casefold() or "capability" in desc


def test_pagination_envelope_extract_reusable_for_projection():
    structured = {
        "items": [{"id": "p1"}, {"id": "p2"}],
        "page": 1,
        "page_size": 40,
        "has_more": True,
        "total_count": 120,
    }
    envelope = extract_pagination_envelope(structured)
    assert envelope is not None
    assert envelope.has_more is True
    assert envelope.page == 1
    assert envelope.page_size == 40


def test_attempt_projection_exposes_owner_pagination_continuation():
    structured = {
        "items": [{"id": f"proc-{i}"} for i in range(40)],
        "page": 1,
        "page_size": 40,
        "has_more": True,
        "total_count": 95,
    }
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text="page of processes",
        structured=structured,
        provenance=SpecialistResultProvenance(
            specialist_id="teo",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="p2",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=False,
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="p2",
        content="page of processes",
        limitations=(LIMITATION_RESULT_TRUNCATED,),
        outcome=outcome,
    )
    projection = _attempt_projection(attempt, observation_index=0)
    assert LIMITATION_RESULT_TRUNCATED in projection["limitations"]
    pagination = projection.get("pagination")
    assert isinstance(pagination, dict), (
        "pagination envelope missing from model-visible observation"
    )
    assert pagination.get("has_more") is True
    assert pagination.get("page") == 1
    assert pagination.get("page_size") == 40
    note = projection.get("continuation_note") or ""
    assert "page" in note.casefold()
    assert "full population" in note.casefold() or "continue" in note.casefold()


def test_attempt_projection_omits_pagination_when_owner_has_none():
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        content_text="scalar fact",
        structured={"data": {"root": {"code": "90260921"}}},
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="p1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=True,
    )
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="p1",
        content="scalar fact",
        limitations=(),
        outcome=outcome,
    )
    projection = _attempt_projection(attempt, observation_index=0)
    assert "pagination" not in projection
    assert "continuation_note" not in projection
