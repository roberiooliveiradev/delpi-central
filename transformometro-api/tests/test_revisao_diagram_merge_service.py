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


def test_build_revisao_view_seeds_from_reference_when_overlay_empty():
    view = RevisaoDiagramMergeService().build_revisao_view(
        macro=_sample_macro(),
        escopo={"inherit_all": True},
        overlay={
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {},
            "edge_overrides": {},
            "removed_node_ids": [],
            "removed_edge_ids": [],
            "extra_nodes": [],
            "extra_edges": [],
        },
        reference_overlay={
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {"n1": {"label": "Da referência", "highlight": "tobe"}},
        },
        reference_meta={"revisao_id": "ref-1", "versao_revisao": "1.0.0"},
    )
    labels = {n["id"]: n["label"] for n in view["flowchart"]["nodes"]}
    assert labels["n1"] == "Da referência"
    assert view["seeded_from_reference"] is True
    assert view["flowchart_base"]["nodes"][0]["label"] == "Entrada"


def test_build_revisao_view_keeps_own_overlay():
    view = RevisaoDiagramMergeService().build_revisao_view(
        macro=_sample_macro(),
        escopo={"inherit_all": True},
        overlay={
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {"n1": {"label": "Desta revisão", "highlight": "tobe"}},
        },
        reference_overlay={
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {"n1": {"label": "Da referência", "highlight": "tobe"}},
        },
        reference_meta={"revisao_id": "ref-1", "versao_revisao": "1.0.0"},
    )
    labels = {n["id"]: n["label"] for n in view["flowchart"]["nodes"]}
    assert labels["n1"] == "Desta revisão"
    assert view["seeded_from_reference"] is False
    assert view["reference_diff"]["changed"] == ["n1"]


def test_apply_overlay_removes_and_adds_nodes_with_lanes():
    service = RevisaoDiagramMergeService()
    result = service.apply_overlay_to_flowchart(
        {
            **_sample_macro(),
            "lanes": [{"id": "lane_old", "label": "Antiga", "height": 168}],
        },
        {
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "removed_node_ids": ["n2"],
            "removed_edge_ids": ["e1"],
            "extra_nodes": [
                {
                    "id": "pro_novo",
                    "type": "process",
                    "label": "Acessar a plataforma",
                    "position": {"x": 100, "y": 40},
                    "lane_id": "lane_new",
                    "highlight": "tobe",
                }
            ],
            "extra_edges": [{"id": "e_new", "from": "n1", "to": "pro_novo", "label": None}],
            "lanes": [
                {"id": "lane_new", "label": "Coleta", "height": 168, "order": 0},
            ],
            "node_overrides": {"n1": {"lane_id": "lane_new", "highlight": "tobe"}},
        },
    )
    ids = {n["id"] for n in result["nodes"]}
    assert ids == {"n1", "pro_novo"}
    assert "n2" not in ids
    assert result["lanes"][0]["id"] == "lane_new"
    assert result["nodes"][0]["lane_id"] == "lane_new"
    assert any(e["id"] == "e_new" for e in result["edges"])


def test_overlay_accepts_extra_edge_to_macro_node_id():
    from tm_app.domain.diagram.flowchart_v1 import validate_overlay_v1

    overlay = validate_overlay_v1(
        {
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "extra_nodes": [
                {
                    "id": "pro_novo",
                    "type": "process",
                    "label": "Novo",
                    "position": {"x": 0, "y": 0},
                }
            ],
            "extra_edges": [{"id": "e_x", "from": "n1", "to": "pro_novo", "label": None}],
        }
    )
    assert overlay["extra_edges"][0]["from"] == "n1"
