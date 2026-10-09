"""G8-COMP-1 — composition conflicts no PREPARE + fingerprint sobre
contributions (revisões deduplicadas continuam seladas)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from tm_app.application.governed_writes import bpmn_migration_capability as cap

PROCESSO = "33333333-3333-3333-3333-333333333333"
USER = SimpleNamespace(id="user-a", sub="user-a", name="User A")


def _linear() -> dict[str, Any]:
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "s", "type": "start", "label": "Início",
             "position": {"x": 0, "y": 0}},
            {"id": "t1", "type": "process", "label": "T1",
             "position": {"x": 200, "y": 0}},
            {"id": "e", "type": "end", "label": "Fim",
             "position": {"x": 400, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "from": "s", "to": "t1", "kind": "sequence",
             "label": None},
            {"id": "e2", "from": "t1", "to": "e", "kind": "sequence",
             "label": None},
        ],
    }


class _FakeDocs:
    def has_active(self, pid):
        return False

    def get_active(self, pid):
        return None


class _FakeRefs:
    def get_active(self, pid):
        return None


def _stack() -> cap.MigrationWriteStack:
    return cap.MigrationWriteStack(
        use_case=None, docs=_FakeDocs(), refs=_FakeRefs(), migrations=None
    )


def _request():
    req = MagicMock()
    req.state.user = USER
    return req


def _composed(flowchart, **extra):
    return {
        "processo_id": PROCESSO,
        "at": "2025-01-01",
        "instancia_id": None,
        "flowchart": flowchart,
        "mermaid": "graph TD",
        "applied_revisoes": [],
        "conflicts": [],
        "provenance": {},
        "contributions": [],
        "base_node_count": len(flowchart.get("nodes") or []),
        **extra,
    }


def test_conflicts_block_prepare_with_governed_error():
    stack = _stack()
    conflicts = [
        {
            "conflict_id": "cc_edge_e_base_1",
            "object_id": "e_base_1",
            "object_kind": "edge",
            "reason": "same_identity_divergent_semantics",
            "contributors": [
                {"revisao_id": "rev-a", "instancia_id": "ia"},
                {"revisao_id": "rev-b", "instancia_id": "ib"},
            ],
        }
    ]
    with (
        patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(_linear(), conflicts=conflicts),
        ),
        patch.object(
            cap.ProcessoRepository, "get", return_value={"nome_processo": "P"}
        ),
        patch.object(cap, "check_processo_manage_access", return_value=None),
    ):
        out = cap.prepare(stack, _request(), {"processo_id": PROCESSO})
    vr = out["validation_result"]
    assert vr["ready"] is False
    report = vr["migration_report"]
    assert report["status"] == "BLOCKED"
    assert report["error_kind"] == "LEGACY_COMPOSITION_CONFLICT"
    assert report["composition_conflicts"][0]["object_id"] == "e_base_1"
    assert out["exact_change"]["candidate_xml"] is None
    assert out["consequential_impact"]["persists"] is False


def test_invalid_composed_flowchart_blocks_without_traceback():
    """FlowchartValidationError do mapper → BLOCKED governado, não 500."""
    stack = _stack()
    bad = {
        "format": "flowchart_v1",
        "nodes": [
            {"id": "dup", "type": "process", "label": "x"},
            {"id": "dup", "type": "process", "label": "x"},
        ],
        "edges": [],
    }
    with (
        patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(bad),
        ),
        patch.object(
            cap.ProcessoRepository, "get", return_value={"nome_processo": "P"}
        ),
        patch.object(cap, "check_processo_manage_access", return_value=None),
    ):
        out = cap.prepare(stack, _request(), {"processo_id": PROCESSO})
    assert out["validation_result"]["ready"] is False
    assert out["validation_result"]["migration_report"]["error_kind"] == (
        "LEGACY_COMPOSITION_INVALID"
    )


def test_fingerprint_covers_deduplicated_contributor():
    """§37: mudar só o overlay B (deduplicado) muda o fingerprint."""
    stack = _stack()
    flowchart = _linear()
    ca = {"revisao_id": "rev-a", "overlay_sha256": "aaa"}
    cb1 = {"revisao_id": "rev-b", "overlay_sha256": "bbb"}
    cb2 = {"revisao_id": "rev-b", "overlay_sha256": "ccc"}

    def _fp(contribs):
        with patch.object(
            cap.DiagramaCompositionService,
            "compose_for_processo",
            return_value=_composed(flowchart, contributions=contribs),
        ):
            return cap._source_fingerprint(stack, PROCESSO)

    fp1 = _fp([ca, cb1])
    fp2 = _fp([ca, cb2])
    assert fp1 != fp2
    assert _fp([ca, cb1]) == fp1
