from __future__ import annotations

from tm_app.application.services.revisao_diagram_merge_service import RevisaoDiagramMergeService


def _sample_macro():
    return {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "n1", "type": "process", "label": "Entrada", "position": {"x": 0, "y": 0}},
            {"id": "n2", "type": "process", "label": "Saída", "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from": "n1", "to": "n2", "label": None}],
    }


def test_merge_applies_scope_subset():
    merged = RevisaoDiagramMergeService().merge(
        macro=_sample_macro(),
        escopo={"node_ids": ["n1"], "inherit_all": False, "include_boundary_edges": False},
        overlay=None,
    )
    assert len(merged["flowchart"]["nodes"]) == 1
    assert merged["flowchart"]["nodes"][0]["id"] == "n1"


def test_merge_applies_overlay_label():
    merged = RevisaoDiagramMergeService().merge(
        macro=_sample_macro(),
        escopo={"inherit_all": True},
        overlay={
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {"n1": {"label": "Entrada revisada", "highlight": "tobe"}},
        },
    )
    labels = [node["label"] for node in merged["flowchart"]["nodes"]]
    assert "Entrada revisada" in labels


def test_diff_detects_label_change():
    diff = RevisaoDiagramMergeService().diff_highlights(
        baseline={
            "nodes": [{"id": "n1", "label": "Antes"}],
            "edges": [],
        },
        current={
            "nodes": [{"id": "n1", "label": "Depois"}],
            "edges": [],
        },
    )
    assert diff["changed"] == ["n1"]
