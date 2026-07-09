from __future__ import annotations

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService


def test_mermaid_empty_diagram():
    text = DiagramMermaidExportService().flowchart_to_mermaid(
        {"format": "flowchart_v1", "format_version": 1, "nodes": [], "edges": []}
    )
    assert "flowchart TD" in text
    assert "vazio" in text.lower()


def test_mermaid_decision_shape():
    text = DiagramMermaidExportService().flowchart_to_mermaid(
        {
            "format": "flowchart_v1",
            "format_version": 1,
            "nodes": [
                {
                    "id": "n_dec",
                    "type": "decision",
                    "label": "Aprovado?",
                    "position": {"x": 0, "y": 0},
                }
            ],
            "edges": [],
        }
    )
    assert 'n_dec{"Aprovado?"}' in text
    assert ":::bpmn_decision" in text
    assert "classDef bpmn_gateway_exclusive" in text
