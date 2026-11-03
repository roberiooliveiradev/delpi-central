"""Doc 217 — composable tool-selection experiment tests (T1–T4)."""
import dataclasses

import pytest

from app.application.capability_provision.capability_retrieval import (
    rank_capabilities,
)
from app.domain.specialist_interop.rules import (
    SpecialistOperationClass,
)


class _Cap:
    def __init__(self, name, desc, cls=SpecialistOperationClass.READ):
        self.remote_name = name
        self.capability_id = f"x.{name}"
        self.description = desc
        self.operation_class = cls
        self.input_schema = {"type": "object"}


class _Group:
    def __init__(self, gid, caps, owner="o", display=""):
        self.group_id = gid
        self.display_name = display or gid
        self.owner_ref = owner
        self.capabilities = tuple(caps)


def _surface(groups):
    out = []
    for k, g in groups.items():
        for c in g.capabilities:
            out.append((k, c))
    return out


def test_retrieval_ranks_semantic_match_first():
    groups = {
        "mcp:caio": _Group(
            "caio",
            [
                _Cap("read", "commercial entities read"),
                _Cap("analyze", "grounded commercial analysis"),
            ],
            display="CAIO commercial",
        ),
        "mcp:teo": _Group(
            "teo", [_Cap("read", "metrology instruments")]
        ),
    }
    ranked = rank_capabilities(
        "commercial analysis of pending deals",
        _surface(groups),
        groups,
    )
    assert ranked[0][0] == "mcp:caio"
    assert ranked[0][1].remote_name == "analyze"


def test_retrieval_multi_tool_recall_preserved():
    groups = {
        "mcp:caio": _Group(
            "caio",
            [
                _Cap("get_context", "context"),
                _Cap("read", "read"),
                _Cap("analyze", "analyze"),
            ],
        ),
        "mcp:suri": _Group("suri", [_Cap("read", "supplies read")]),
    }
    ranked = rank_capabilities(
        "read and analyze commercial data",
        _surface(groups),
        groups,
        top_k=5,
    )
    names = {c.remote_name for _, c in ranked}
    assert {"read", "analyze"} <= names  # both needed tools recalled


def test_retrieval_empty_query_returns_bounded():
    groups = {"g": _Group("g", [_Cap("a", "x"), _Cap("b", "y")])}
    ranked = rank_capabilities("", _surface(groups), groups)
    assert len(ranked) == 2


def test_live_mode_untouched_groups():
    """Variant A invariant: mode 'live' never filters the surface."""
    import app.application.capability_provision.orchestration as orch_mod

    orch = object.__new__(orch_mod.OperationalCapabilityOrchestrator)
    orch._tool_selection_mode = "live"
    groups = {"g": _Group("g", [_Cap("a", "x")])}
    assert orch._filter_groups_for_selection("q", groups) is groups


def test_retrieval_mode_filters_groups():
    import app.application.capability_provision.orchestration as orch_mod

    orch = object.__new__(orch_mod.OperationalCapabilityOrchestrator)
    orch._tool_selection_mode = "retrieval_llm"
    groups = {
        "mcp:caio": _Group("caio", [_Cap("analyze", "commercial analysis")]),
        "mcp:suri": _Group(
            "suri", [_Cap("read", "wood screw inventory supplies")]
        ),
    }
    kept = orch._filter_groups_for_selection(
        "analyze commercial performance", groups
    )
    assert "mcp:caio" in kept


def test_compact_payload_hides_argument_shape():
    from app.application.capability_provision.orchestration import (
        _capability_payload,
    )
    import json

    group = _Group("g", [_Cap("read", "read entities")])
    full = json.loads(_capability_payload(group))
    compact = json.loads(_capability_payload(group, compact=True))
    assert "argument_keys" in full[0]
    assert "argument_keys" not in compact[0]
    assert "required" not in compact[0]
