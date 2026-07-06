from __future__ import annotations

import pytest

from tm_app.domain.diagram.flowchart_v1 import (
    FlowchartValidationError,
    empty_flowchart,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)


def test_empty_flowchart_valid():
    doc = validate_flowchart_v1(empty_flowchart())
    assert doc["format"] == "flowchart_v1"
    assert doc["nodes"] == []


def test_flowchart_rejects_duplicate_node_ids():
    doc = {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "n1", "type": "process", "label": "A", "position": {"x": 0, "y": 0}},
            {"id": "n1", "type": "process", "label": "B", "position": {"x": 10, "y": 0}},
        ],
        "edges": [],
    }
    with pytest.raises(FlowchartValidationError, match="duplicado"):
        validate_flowchart_v1(doc)


def test_flowchart_rejects_edge_to_missing_node():
    doc = {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "n1", "type": "process", "label": "A", "position": {"x": 0, "y": 0}},
        ],
        "edges": [{"id": "e1", "from": "n1", "to": "n2", "label": None}],
    }
    with pytest.raises(FlowchartValidationError, match="from inválido|to inválido"):
        validate_flowchart_v1(doc)


def test_escopo_rejects_unknown_node():
    with pytest.raises(FlowchartValidationError, match="fora do macro"):
        validate_escopo(
            {"node_ids": ["n_x"], "inherit_all": False},
            macro_node_ids={"n1"},
        )


def test_overlay_valid_minimal():
    overlay = validate_overlay_v1(
        {
            "format": "flowchart_overlay_v1",
            "format_version": 1,
            "node_overrides": {"n1": {"label": "Novo", "highlight": "tobe"}},
        }
    )
    assert overlay["node_overrides"]["n1"]["highlight"] == "tobe"


def test_flowchart_accepts_swimlanes_and_routing():
    lane_id = "lane_comercial"
    doc = validate_flowchart_v1(
        {
            "format": "flowchart_v1",
            "format_version": 1,
            "lanes": [{"id": lane_id, "label": "Comercial", "height": 168}],
            "nodes": [
                {
                    "id": "n_start",
                    "type": "start",
                    "label": "Início",
                    "lane_id": lane_id,
                    "position": {"x": 160, "y": 60},
                },
                {
                    "id": "n_proc",
                    "type": "process",
                    "label": "Atividade",
                    "lane_id": lane_id,
                    "position": {"x": 320, "y": 50},
                    "meta": {"manual": True},
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "from": "n_start",
                    "to": "n_proc",
                    "label": None,
                    "routing": "smoothstep",
                }
            ],
        }
    )
    assert doc["lanes"][0]["id"] == lane_id
