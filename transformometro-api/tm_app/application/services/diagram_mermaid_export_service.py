from __future__ import annotations

import re
from typing import Any

from tm_app.domain.diagram.bpmn_mermaid_mapping import (
    bpmn_mermaid_class_for_type,
    format_mermaid_node_line,
    mermaid_class_def_lines,
    mermaid_edge_syntax,
)
from tm_app.domain.diagram.bpmn_node_catalog import normalize_node_type


def _sanitize_mermaid_id(node_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", node_id)
    if not cleaned:
        return "node"
    if cleaned[0].isdigit():
        return f"n_{cleaned}"
    return cleaned


def _escape_label(label: str) -> str:
    return label.replace('"', "'").replace("\n", " ").strip()


def _lane_subgraph_id(lane_id: str) -> str:
    return _sanitize_mermaid_id(f"lane_{lane_id}")


class DiagramMermaidExportService:
    def flowchart_to_mermaid(self, flowchart: dict[str, Any]) -> str:
        nodes = flowchart.get("nodes") or []
        edges = flowchart.get("edges") or []
        lanes = flowchart.get("lanes") or []
        if not nodes:
            return "flowchart TD\n    empty[\"Diagrama vazio\"]"

        lines = ["flowchart TD"]
        id_map: dict[str, str] = {}
        used_classes: set[str] = set()

        def write_node(node: dict[str, Any], indent: str) -> None:
            if not isinstance(node, dict):
                return
            raw_id = str(node.get("id") or "")
            if not raw_id:
                return
            node_type = normalize_node_type(str(node.get("type") or "process"))
            mermaid_id = _sanitize_mermaid_id(raw_id)
            id_map[raw_id] = mermaid_id
            line = format_mermaid_node_line(
                node_type,
                mermaid_id,
                str(node.get("label") or raw_id),
            )
            used_classes.add(bpmn_mermaid_class_for_type(node_type))
            highlight = node.get("highlight") or (node.get("meta") or {}).get("highlight")
            if highlight in {"asis", "tobe", "changed", "removed"}:
                line = f"{line} highlight_{highlight}"
            lines.append(f"{indent}{line}")

        if lanes:
            lane_ids = {str(lane.get("id")) for lane in lanes if isinstance(lane, dict) and lane.get("id")}
            nodes_by_lane: dict[str, list[dict[str, Any]]] = {}
            unassigned: list[dict[str, Any]] = []

            for node in nodes:
                if not isinstance(node, dict):
                    continue
                lane_id = str(node.get("lane_id") or "")
                if lane_id and lane_id in lane_ids:
                    nodes_by_lane.setdefault(lane_id, []).append(node)
                else:
                    unassigned.append(node)

            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                lane_id = str(lane.get("id") or "")
                if not lane_id:
                    continue
                lane_nodes = nodes_by_lane.get(lane_id) or []
                if not lane_nodes:
                    continue
                label = _escape_label(str(lane.get("label") or lane_id))
                lines.append(f'    subgraph {_lane_subgraph_id(lane_id)} ["{label}"]')
                for node in lane_nodes:
                    write_node(node, "        ")
                lines.append("    end")

            for node in unassigned:
                write_node(node, "    ")
        else:
            for node in nodes:
                write_node(node, "    ")

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id not in id_map or to_id not in id_map:
                continue
            kind = str(edge.get("kind") or "sequence")
            label = edge.get("label")
            lines.append(
                mermaid_edge_syntax(
                    id_map[from_id],
                    id_map[to_id],
                    kind if kind in {"sequence", "message_flow", "association"} else "sequence",
                    str(label) if label else None,
                )
            )

        lines.extend(mermaid_class_def_lines(used_classes))

        highlights = {
            node.get("highlight")
            for node in nodes
            if isinstance(node, dict) and node.get("highlight") in {"asis", "tobe", "changed", "removed"}
        }
        if highlights:
            lines.append("    classDef highlight_asis fill:#fef3c7,stroke:#d97706")
            lines.append("    classDef highlight_tobe fill:#dbeafe,stroke:#2563eb")
            lines.append("    classDef highlight_changed fill:#fce7f3,stroke:#db2777")
            lines.append("    classDef highlight_removed fill:#f3f4f6,stroke:#9ca3af,stroke-dasharray:4")

        return "\n".join(lines)
