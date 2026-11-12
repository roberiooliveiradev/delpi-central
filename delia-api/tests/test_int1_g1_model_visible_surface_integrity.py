"""INT-1 G1 — deterministic integrity of model-visible tool surface.

Proves composition boundaries that forensics need before attributing
first-tool choice to the external model:

1. TEO process-WBS clarification survives ``_EnvelopeHintedToolset``.
2. Catalog snapshot capture no longer hard-slices descriptions to 500.
3. No specialist routing keywords are injected by composition.

Does **not** claim Qwen would select DAVI — only that information
delivery is intact for selection.
"""

from __future__ import annotations

import asyncio
import dataclasses

from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _EnvelopeHintedToolset,
)
from scripts.int1_openrouter_qwen14b_instrumented_eval import _catalog_snapshot
from scripts.int1_secure_decision_trace import sanitize_mapping


_TEO_READ_DESC = (
    "Semantic read — never writes. entity + typed action + params "
    "object. Domain entities (process, instance, revision, "
    "measurement, investment, shared_resource, resource_cost, "
    "resource_link, meeting_minute, process_document, "
    "decomposition_tree (process WBS/decomposition tree; "
    "id=processo_id — hierarchical process mapeamento macro, "
    "not a materials/product bill-of-materials), "
    "instance_decomposition_scope, "
    "revision_decomposition_overlay, process_diagram): "
    "action=search|get — search lists records; get fetches ONE "
    "record and requires params.id. "
    + ("padding-" * 80)
)


@dataclasses.dataclass
class _FakeDef:
    description: str
    parameters_json_schema: dict


@dataclasses.dataclass
class _FakeTool:
    tool_def: _FakeDef


def test_envelope_hint_preserves_teo_process_wbs_clarification() -> None:
    assert "process WBS" in _TEO_READ_DESC
    assert "bill-of-materials" in _TEO_READ_DESC
    assert len(_TEO_READ_DESC) > 500

    class _Wrapped:
        async def get_tools(self, ctx):
            return {
                "teo.read": _FakeTool(
                    _FakeDef(
                        _TEO_READ_DESC,
                        {
                            "type": "object",
                            "properties": {
                                "entity": {"type": "string"},
                                "action": {"type": "string"},
                                "params": {"type": "object"},
                            },
                        },
                    )
                )
            }

    tools = asyncio.run(_EnvelopeHintedToolset(_Wrapped()).get_tools(None))
    desc = tools["teo.read"].tool_def.description or ""
    assert "process WBS" in desc
    assert "processo_id" in desc
    assert "bill-of-materials" in desc.lower()
    assert "davi" not in desc.lower()
    assert "use DAVI" not in desc


def test_catalog_snapshot_preserves_full_teo_wbs_description() -> None:
    """Harness capture must not hide WBS markers via hard [:500]."""
    live = [
        {
            "capability_id": "teo.read",
            "remote_name": "read",
            "specialist_id": "teo",
            "operation_class": "READ",
            "description": _TEO_READ_DESC,
            "input_schema": {"type": "object"},
        },
        {
            "capability_id": "davi.read",
            "remote_name": "read",
            "specialist_id": "davi",
            "operation_class": "READ",
            "description": (
                "Semantic read for governed capabilities "
                "(e.g. get_product_structure)."
            ),
            "input_schema": {"type": "object"},
        },
    ]
    snap = _catalog_snapshot(live)
    teo = next(t for t in snap["tools"] if t["capability_id"] == "teo.read")
    assert teo["description_len"] == len(_TEO_READ_DESC)
    assert teo["description_has_process_wbs"] is True
    assert teo["description_has_bom_negative"] is True
    assert "process WBS" in teo["description"]
    assert snap["capture_boundary"] == "catalog_projection_pre_envelope_hint"
    # Sanitizer keeps tool descriptions beyond the generic 500-char cap.
    sanitized = sanitize_mapping(teo)
    assert "process WBS" in sanitized["description"]
    assert "bill-of-materials" in sanitized["description"].lower()
    assert "davi.read" in snap["model_visible_tool_names"]
