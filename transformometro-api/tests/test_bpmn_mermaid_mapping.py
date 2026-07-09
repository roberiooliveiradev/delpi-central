from __future__ import annotations

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService
from tm_app.domain.diagram.bpmn_mermaid_mapping import (
    bpmn_mermaid_class_for_type,
    build_bpmn_catalog_for_api,
    format_mermaid_node_line,
)


def test_format_mermaid_node_line_includes_bpmn_class():
    line = format_mermaid_node_line("start_timer", "n1", "Agendar")
    assert '(("Agendar"))' in line
    assert ":::bpmn_start_timer" in line


def test_mermaid_export_swimlanes_and_classes():
    text = DiagramMermaidExportService().flowchart_to_mermaid(
        {
            "format": "flowchart_v1",
            "format_version": 1,
            "lanes": [{"id": "comercial", "label": "Comercial", "height": 168, "order": 0}],
            "nodes": [
                {
                    "id": "n1",
                    "type": "start_message",
                    "label": "Pedido",
                    "position": {"x": 0, "y": 0},
                    "lane_id": "comercial",
                }
            ],
            "edges": [],
        }
    )
    assert 'subgraph lane_comercial ["Comercial"]' in text
    assert ":::bpmn_start_message" in text
    assert "classDef bpmn_event_start" in text


def test_build_bpmn_catalog_for_api():
    catalog = build_bpmn_catalog_for_api()
    assert catalog["format"] == "transformometro_bpmn_catalog_v1"
    assert len(catalog["node_types"]) >= 50
    start_timer = next(item for item in catalog["node_types"] if item["id"] == "start_timer")
    assert start_timer["label"] == "Início — timer"
    assert start_timer["mermaid"]["class"] == bpmn_mermaid_class_for_type("start_timer")
