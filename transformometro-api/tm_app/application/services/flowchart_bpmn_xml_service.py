from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from xml.dom import minidom

from tm_app.domain.diagram.flowchart_v1 import FlowchartValidationError, validate_flowchart_v1

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"

NS = {
    "bpmn": BPMN_NS,
    "bpmndi": BPMNDI_NS,
    "dc": DC_NS,
}

NODE_TO_BPMN = {
    "start": "startEvent",
    "end": "endEvent",
    "process": "task",
    "document": "task",
    "data": "task",
    "subprocess": "subProcess",
    "decision": "exclusiveGateway",
    "comment": "task",
}


def _sanitize_xml_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", value)
    if not cleaned:
        return "Element_1"
    if cleaned[0].isdigit():
        return f"Id_{cleaned}"
    return cleaned


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class FlowchartBpmnXmlService:
    def export_xml(self, flowchart: dict[str, Any], *, process_name: str = "Processo") -> str:
        doc = validate_flowchart_v1(flowchart)
        nodes = doc.get("nodes") or []
        edges = doc.get("edges") or []
        lanes = doc.get("lanes") or []

        ET.register_namespace("bpmn", BPMN_NS)
        ET.register_namespace("bpmndi", BPMNDI_NS)
        ET.register_namespace("dc", DC_NS)
        ET.register_namespace("xsi", XSI_NS)

        root = ET.Element(f"{{{BPMN_NS}}}definitions", attrib={"id": "Definitions_1"})
        process_el = ET.SubElement(
            root,
            f"{{{BPMN_NS}}}process",
            attrib={"id": "Process_1", "name": _xml_escape(process_name), "isExecutable": "false"},
        )

        lane_by_node: dict[str, str] = {}
        if lanes:
            lane_set = ET.SubElement(process_el, f"{{{BPMN_NS}}}laneSet", attrib={"id": "LaneSet_1"})
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                lane_id = _sanitize_xml_id(str(lane.get("id") or "lane"))
                lane_el = ET.SubElement(
                    lane_set,
                    f"{{{BPMN_NS}}}lane",
                    attrib={"id": lane_id, "name": _xml_escape(str(lane.get("label") or lane_id))},
                )
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    if str(node.get("lane_id") or "") == str(lane.get("id") or ""):
                        node_id = _sanitize_xml_id(str(node.get("id")))
                        lane_by_node[str(node["id"])] = lane_id
                        ET.SubElement(lane_el, f"{{{BPMN_NS}}}flowNodeRef").text = node_id

        for node in nodes:
            if not isinstance(node, dict) or not node.get("id"):
                continue
            node_type = str(node.get("type") or "process")
            bpmn_type = NODE_TO_BPMN.get(node_type, "task")
            attrs = {
                "id": _sanitize_xml_id(str(node["id"])),
                "name": _xml_escape(str(node.get("label") or node["id"])),
            }
            if bpmn_type == "task" and node_type == "process" and node.get("meta", {}).get("manual"):
                attrs["isForCompensation"] = "false"
            ET.SubElement(process_el, f"{{{BPMN_NS}}}{bpmn_type}", attrib=attrs)

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            from_id = edge.get("from")
            to_id = edge.get("to")
            if not from_id or not to_id:
                continue
            attrs = {
                "id": _sanitize_xml_id(str(edge.get("id") or f"{from_id}_{to_id}")),
                "sourceRef": _sanitize_xml_id(str(from_id)),
                "targetRef": _sanitize_xml_id(str(to_id)),
            }
            label = edge.get("label")
            if label:
                attrs["name"] = _xml_escape(str(label))
            ET.SubElement(process_el, f"{{{BPMN_NS}}}sequenceFlow", attrib=attrs)

        rough = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ")

    def import_xml(self, xml_text: str) -> dict[str, Any]:
        if not xml_text.strip():
            raise FlowchartValidationError("XML BPMN vazio.")

        root = ET.fromstring(xml_text)
        process = self._find_process(root)
        if process is None:
            raise FlowchartValidationError("Nenhum processo BPMN encontrado no XML.")

        lanes: list[dict[str, Any]] = []
        lane_set = process.find("bpmn:laneSet", NS) or process.find(f"{{{BPMN_NS}}}laneSet")
        lane_node_map: dict[str, str] = {}
        if lane_set is not None:
            lane_elements = lane_set.findall("bpmn:lane", NS) or lane_set.findall(
                f"{{{BPMN_NS}}}lane"
            )
            for index, lane_el in enumerate(lane_elements):
                lane_id = lane_el.get("id") or f"lane_{index}"
                lanes.append(
                    {
                        "id": lane_id,
                        "label": lane_el.get("name") or lane_id,
                        "height": 168,
                        "order": index,
                    }
                )
                refs = lane_el.findall("bpmn:flowNodeRef", NS) or lane_el.findall(
                    f"{{{BPMN_NS}}}flowNodeRef"
                )
                for ref in refs:
                    if ref.text:
                        lane_node_map[ref.text.strip()] = lane_id

        bpmn_to_type = {
            "startEvent": "start",
            "endEvent": "end",
            "task": "process",
            "subProcess": "subprocess",
            "exclusiveGateway": "decision",
            "parallelGateway": "decision",
            "inclusiveGateway": "decision",
        }

        nodes: list[dict[str, Any]] = []
        x_offset = 160
        y_base = 80
        for index, child in enumerate(list(process)):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in {"laneSet", "sequenceFlow"}:
                continue
            if tag not in bpmn_to_type and tag not in NODE_TO_BPMN.values():
                continue
            node_id = child.get("id")
            if not node_id:
                continue
            node_type = bpmn_to_type.get(tag, "process")
            lane_id = lane_node_map.get(node_id)
            y = y_base + (index % 3) * 96
            if lane_id and lanes:
                lane_index = next(
                    (idx for idx, lane in enumerate(lanes) if lane["id"] == lane_id), 0
                )
                y = 56 + lane_index * 168
            nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "label": child.get("name") or node_id,
                    "position": {"x": x_offset + (index // 3) * 220, "y": y},
                    **({"lane_id": lane_id} if lane_id else {}),
                    **(
                        {"meta": {"manual": True}}
                        if node_type == "process"
                        else {}
                    ),
                }
            )

        node_ids = {node["id"] for node in nodes}
        edges: list[dict[str, Any]] = []
        flows = process.findall("bpmn:sequenceFlow", NS) or process.findall(
            f"{{{BPMN_NS}}}sequenceFlow"
        )
        for flow in flows:
            from_id = flow.get("sourceRef")
            to_id = flow.get("targetRef")
            if not from_id or not to_id or from_id not in node_ids or to_id not in node_ids:
                continue
            edges.append(
                {
                    "id": flow.get("id") or f"flow_{from_id}_{to_id}",
                    "from": from_id,
                    "to": to_id,
                    "label": flow.get("name"),
                    "routing": "smoothstep",
                }
            )

        payload: dict[str, Any] = {
            "format": "flowchart_v1",
            "format_version": 1,
            "nodes": nodes,
            "edges": edges,
        }
        if lanes:
            payload["lanes"] = lanes
        return validate_flowchart_v1(payload)

    @staticmethod
    def _find_process(root: ET.Element) -> ET.Element | None:
        for el in root.iter():
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if tag == "process":
                return el
        return None
