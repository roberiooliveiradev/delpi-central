"""G8-COMP-1 — cross-instance equivalent contributions: semantic dedup +
provenance; divergent same-id contributions → composition conflict."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from tm_app.application.services.diagram_composition_service import (
    DiagramaCompositionService,
)
from tm_app.domain.diagram.flowchart_v1 import validate_flowchart_v1
from tm_app.domain.diagram.legacy_bpmn_migration import LegacyFlowchartToBpmnMapper


def _macro():
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "start", "type": "start", "label": "Início",
             "lane_id": "l1", "position": {"x": 40, "y": 20}},
            {"id": "n1", "type": "process", "label": "Etapa 1",
             "lane_id": "l1", "position": {"x": 200, "y": 20}},
            {"id": "end", "type": "end", "label": "Fim",
             "lane_id": "l1", "position": {"x": 400, "y": 20}},
        ],
        "edges": [
            {"id": "e0", "from": "start", "to": "n1", "kind": "sequence",
             "label": None},
            {"id": "e9", "from": "n1", "to": "end", "kind": "sequence",
             "label": None},
        ],
        "lanes": [{"id": "l1", "label": "Lane", "order": 0, "height": 160}],
    }


def _overlay(
    *,
    extra_nodes=None,
    extra_edges=None,
    node_overrides=None,
    edge_overrides=None,
    removed_node_ids=None,
    removed_edge_ids=None,
):
    doc = {"format": "flowchart_overlay_v1", "format_version": 1}
    if extra_nodes is not None:
        doc["extra_nodes"] = extra_nodes
    if extra_edges is not None:
        doc["extra_edges"] = extra_edges
    if node_overrides is not None:
        doc["node_overrides"] = node_overrides
    if edge_overrides is not None:
        doc["edge_overrides"] = edge_overrides
    if removed_node_ids is not None:
        doc["removed_node_ids"] = removed_node_ids
    if removed_edge_ids is not None:
        doc["removed_edge_ids"] = removed_edge_ids
    return doc


REV_A = {
    "revisao_id": "rev-a",
    "instancia_id": "inst-a",
    "versao_revisao": "1.0.0",
    "cenario_tipo": "melhoria",
    "data_inicio_vigencia": "2026-01-01",
    "data_fim_vigencia": None,
    "deletado": False,
}
REV_B = {
    "revisao_id": "rev-b",
    "instancia_id": "inst-b",
    "versao_revisao": "1.0.0",
    "cenario_tipo": "melhoria",
    "data_inicio_vigencia": "2026-01-01",
    "data_fim_vigencia": None,
    "deletado": False,
}


def _compose(overlays: dict[str, dict], revisoes=None, macro=None):
    """Compose with patched repositories; overlays keyed by revisao_id."""
    revisoes = revisoes if revisoes is not None else [REV_A, REV_B]
    with patch(
        "tm_app.application.services.diagram_composition_service.ProcessoDiagramRepository"
    ) as proc, patch(
        "tm_app.application.services.diagram_composition_service.RevisaoRepository"
    ) as rev, patch(
        "tm_app.application.services.diagram_composition_service.InstanciaDiagramEscopoRepository"
    ) as escopo, patch(
        "tm_app.application.services.diagram_composition_service.RevisaoDiagramOverlayRepository"
    ) as ov:
        proc.return_value.get.return_value = {"conteudo": macro or _macro()}
        rev.return_value.list_by_processo.return_value = revisoes
        escopo.return_value.get.return_value = {
            "node_ids": [],
            "inherit_all": True,
            "include_boundary_edges": False,
        }
        ov.return_value.get.side_effect = lambda rid: (
            {"conteudo": overlays[rid]} if rid in overlays else None
        )
        return DiagramaCompositionService().compose_for_processo(
            "p1", at=date(2026, 5, 1)
        )


# --- PROC-0067 real-shape fixture --------------------------------------------

_PROC0067_EXTRA_NODE = {
    "id": "bases_corporativas",
    "type": "process",
    "label": "Dados são registrados nas bases corporativas",
    "lane_id": "l1",
    "position": {"x": 120, "y": 20},
}
_PROC0067_EDGES = [
    {"id": "e_base_1", "from": "start", "to": "bases_corporativas",
     "kind": "sequence", "label": None},
    {"id": "e_base_2", "from": "bases_corporativas", "to": "n1",
     "kind": "sequence", "label": None},
]


def test_proc0067_equivalent_overlays_dedup_to_single_elements():
    """CASE 1+2 + PROC-0067: same id + same semantics → 1 element + 2
    provenance contributors."""
    overlays = {
        "rev-a": _overlay(
            extra_nodes=[_PROC0067_EXTRA_NODE],
            extra_edges=_PROC0067_EDGES,
        ),
        "rev-b": _overlay(
            extra_nodes=[dict(_PROC0067_EXTRA_NODE)],
            extra_edges=[dict(e) for e in _PROC0067_EDGES],
        ),
    }
    result = _compose(overlays)

    nodes = {n["id"] for n in result["flowchart"]["nodes"]}
    edges = {e["id"] for e in result["flowchart"]["edges"]}
    assert "bases_corporativas" in nodes
    assert len([n for n in result["flowchart"]["nodes"] if n["id"] == "bases_corporativas"]) == 1
    assert len([e for e in result["flowchart"]["edges"] if e["id"] == "e_base_1"]) == 1
    assert len([e for e in result["flowchart"]["edges"] if e["id"] == "e_base_2"]) == 1
    assert "e_base_1" in edges and "e_base_2" in edges

    # composed output must pass the canonical validator and the mapper
    validate_flowchart_v1(result["flowchart"])
    candidate = LegacyFlowchartToBpmnMapper().map(
        result["flowchart"], process_name="Gerenciamento de Rotina"
    )
    assert "e_base_1" in candidate.bpmn_xml
    assert result["conflicts"] == []

    # provenance keeps both contributors — exactly one entry each
    for element_id in ("bases_corporativas", "e_base_1", "e_base_2"):
        entries = result["provenance"][element_id]
        contrib_ids = [c["revisao_id"] for c in entries]
        assert sorted(contrib_ids) == ["rev-a", "rev-b"]
        assert sum(1 for c in entries if c.get("deduplicated")) == 1

    # contributions keep both revisions fingerprintable
    assert {c["revisao_id"] for c in result["contributions"]} == {
        "rev-a",
        "rev-b",
    }


def test_case3_same_node_id_divergent_label_conflicts():
    overlays = {
        "rev-a": _overlay(extra_nodes=[
            {"id": "nx", "type": "process", "label": "Versão A",
             "position": {"x": 1, "y": 1}},
        ]),
        "rev-b": _overlay(extra_nodes=[
            {"id": "nx", "type": "process", "label": "Versão B",
             "position": {"x": 1, "y": 1}},
        ]),
    }
    result = _compose(overlays)
    assert len([n for n in result["flowchart"]["nodes"] if n["id"] == "nx"]) == 1
    conflict = [c for c in result["conflicts"] if c.get("object_id") == "nx"]
    assert len(conflict) == 1
    assert conflict[0]["reason"] == "same_identity_divergent_semantics"
    assert conflict[0]["object_kind"] == "node"
    assert {c["revisao_id"] for c in conflict[0]["contributors"]} == {
        "rev-a", "rev-b",
    }


def test_case4_same_edge_id_divergent_target_conflicts():
    overlays = {
        "rev-a": _overlay(extra_edges=[
            {"id": "ex", "from": "start", "to": "n1", "kind": "sequence"},
        ]),
        "rev-b": _overlay(extra_edges=[
            {"id": "ex", "from": "start", "to": "end", "kind": "sequence"},
        ]),
    }
    result = _compose(overlays)
    assert len([e for e in result["flowchart"]["edges"] if e["id"] == "ex"]) == 1
    conflict = [c for c in result["conflicts"] if c.get("object_id") == "ex"]
    assert len(conflict) == 1
    assert conflict[0]["object_kind"] == "edge"
    assert conflict[0]["reason"] == "same_identity_divergent_semantics"


def test_case5_same_override_same_value_dedup_no_conflict():
    ov = {"n1": {"label": "Mesmo valor"}}
    result = _compose(
        {"rev-a": _overlay(node_overrides=ov),
         "rev-b": _overlay(node_overrides=dict(ov))}
    )
    labels = {n["id"]: n["label"] for n in result["flowchart"]["nodes"]}
    assert labels["n1"] == "Mesmo valor"
    assert result["conflicts"] == []
    # equivalent override keeps both contributors in provenance
    entries = result["provenance"]["n1"]
    assert sorted(c["revisao_id"] for c in entries) == ["rev-a", "rev-b"]
    assert sum(1 for c in entries if c.get("deduplicated")) == 1


def test_case6_same_override_divergent_value_conflicts():
    result = _compose({
        "rev-a": _overlay(node_overrides={"n1": {"label": "A"}}),
        "rev-b": _overlay(node_overrides={"n1": {"label": "B"}}),
    })
    assert len(result["conflicts"]) == 1
    assert result["conflicts"][0]["node_id"] == "n1"


def test_case7_same_remove_dedup_no_conflict():
    ov = ["n1"]
    result = _compose({
        "rev-a": _overlay(removed_node_ids=ov),
        "rev-b": _overlay(removed_node_ids=list(ov)),
    })
    ids = {n["id"] for n in result["flowchart"]["nodes"]}
    assert "n1" not in ids
    assert result["conflicts"] == []
    contrib = {c["revisao_id"] for c in result["provenance"]["n1"]}
    assert contrib == {"rev-a", "rev-b"}


def test_case8_remove_then_modify_is_conflict():
    result = _compose({
        "rev-a": _overlay(removed_node_ids=["n1"]),
        "rev-b": _overlay(node_overrides={"n1": {"label": "B"}}),
    })
    conflict = [c for c in result["conflicts"]
                if c.get("object_id") == "n1" and c.get("reason") == "remove_vs_modify"]
    assert len(conflict) == 1


def test_modify_then_remove_is_conflict():
    result = _compose({
        "rev-a": _overlay(node_overrides={"n1": {"label": "A"}}),
        "rev-b": _overlay(removed_node_ids=["n1"]),
    })
    conflict = [
        c for c in result["conflicts"]
        if (c.get("object_id") or c.get("node_id")) == "n1"
    ]
    assert len(conflict) == 1


def test_order_determinism_swapped_revision_order():
    overlays = {
        "rev-a": _overlay(
            extra_nodes=[_PROC0067_EXTRA_NODE], extra_edges=_PROC0067_EDGES
        ),
        "rev-b": _overlay(
            extra_nodes=[dict(_PROC0067_EXTRA_NODE)],
            extra_edges=[dict(e) for e in _PROC0067_EDGES],
        ),
    }
    r1 = _compose(overlays)
    r2 = _compose(overlays, revisoes=[REV_B, REV_A])
    assert r1["flowchart"] == r2["flowchart"]
    assert r1["provenance"] == r2["provenance"]
    assert [c["overlay_sha256"] for c in r1["contributions"]] == [
        c["overlay_sha256"] for c in r2["contributions"]
    ]


def test_equivalent_dedup_geometry_divergence_reported_not_hidden():
    overlays = {
        "rev-a": _overlay(extra_nodes=[_PROC0067_EXTRA_NODE]),
        "rev-b": _overlay(extra_nodes=[
            {**_PROC0067_EXTRA_NODE, "position": {"x": 999, "y": 999}},
        ]),
    }
    result = _compose(overlays)
    assert result["conflicts"] == []
    divergence = [
        n for n in result["composition_notes"]
        if n.get("reason") == "geometry_divergence"
        and n.get("element_id") == "bases_corporativas"
    ]
    assert len(divergence) == 1


def test_edge_override_divergence_conflicts():
    result = _compose({
        "rev-a": _overlay(edge_overrides={"e0": {"label": "A"}}),
        "rev-b": _overlay(edge_overrides={"e0": {"label": "B"}}),
    })
    conflict = [c for c in result["conflicts"] if c.get("object_id") == "e0"]
    assert len(conflict) == 1
    assert conflict[0]["object_kind"] == "edge"
