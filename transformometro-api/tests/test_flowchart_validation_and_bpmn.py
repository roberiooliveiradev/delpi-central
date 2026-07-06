from __future__ import annotations

from tm_app.application.services.flowchart_bpmn_xml_service import FlowchartBpmnXmlService
from tm_app.domain.diagram.flowchart_validation_service import FlowchartValidationService


def test_validation_detects_unreachable_and_dead_end():
    service = FlowchartValidationService()
    report = service.validate(
        {
            "format": "flowchart_v1",
            "format_version": 1,
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "label": "Início",
                    "position": {"x": 0, "y": 0},
                },
                {
                    "id": "orphan",
                    "type": "process",
                    "label": "Órfão",
                    "position": {"x": 100, "y": 0},
                },
                {
                    "id": "dead",
                    "type": "process",
                    "label": "Sem saída",
                    "position": {"x": 200, "y": 0},
                },
            ],
            "edges": [
                {"id": "e1", "from": "start", "to": "dead", "label": None},
            ],
        }
    )
    codes = {item["code"] for item in report["issues"]}
    assert "unreachable_node" in codes
    assert "dead_end" in codes
    assert report["simulation"]["stuck_count"] >= 1


def test_bpmn_xml_round_trip_minimal():
    service = FlowchartBpmnXmlService()
    original = {
        "format": "flowchart_v1",
        "format_version": 1,
        "nodes": [
            {"id": "start_1", "type": "start", "label": "Início", "position": {"x": 0, "y": 0}},
            {"id": "task_1", "type": "process", "label": "Atividade", "position": {"x": 120, "y": 0}},
            {"id": "end_1", "type": "end", "label": "Fim", "position": {"x": 240, "y": 0}},
        ],
        "edges": [
            {"id": "f1", "from": "start_1", "to": "task_1", "label": None, "routing": "smoothstep"},
            {"id": "f2", "from": "task_1", "to": "end_1", "label": None, "routing": "smoothstep"},
        ],
    }
    xml_text = service.export_xml(original, process_name="Teste")
    assert "startEvent" in xml_text
    assert "sequenceFlow" in xml_text
    imported = service.import_xml(xml_text)
    assert len(imported["nodes"]) == 3
    assert len(imported["edges"]) == 2
