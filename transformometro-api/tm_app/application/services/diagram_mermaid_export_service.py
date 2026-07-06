from __future__ import annotations

import re
from typing import Any

from tm_app.domain.diagram.flowchart_v1 import NODE_TYPES


def _sanitize_mermaid_id(node_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", node_id)
    if not cleaned:
        return "node"
    if cleaned[0].isdigit():
        return f"n_{cleaned}"
    return cleaned


def _escape_label(label: str) -> str:
    return label.replace('"', "'").replace("\n", " ").strip()


def _node_shape(node_type: str, mermaid_id: str, label: str) -> str:
    text = _escape_label(label)
    if node_type == "decision":
        return f'    {mermaid_id}{{"{text}"}}'
    if node_type in {"start", "end"}:
        return f'    {mermaid_id}(("{text}"))'
    if node_type == "comment":
        return f'    {mermaid_id}[/"{text}"/]'
    return f'    {mermaid_id}["{text}"]'


class DiagramMermaidExportService:
    def flowchart_to_mermaid(self, flowchart: dict[str, Any]) -> str:
        nodes = flowchart.get("nodes") or []
        edges = flowchart.get("edges") or []
        if not nodes:
            return "flowchart TD\n    empty[\"Diagrama vazio\"]"

        lines = ["flowchart TD"]
        id_map: dict[str, str] = {}

        for node in nodes:
            if not isinstance(node, dict):
                continue
            raw_id = str(node.get("id") or "")
            if not raw_id:
                continue
            node_type = str(node.get("type") or "process")
            if node_type not in NODE_TYPES:
                node_type = "process"
            mermaid_id = _sanitize_mermaid_id(raw_id)
            id_map[raw_id] = mermaid_id
            highlight = (node.get("highlight") or node.get("meta", {}).get("highlight"))
            line = _node_shape(node_type, mermaid_id, str(node.get("label") or raw_id))
            if highlight in {"asis", "tobe", "changed", "removed"}:
                line = f"{line}:::highlight_{highlight}"
            lines.append(line)

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id not in id_map or to_id not in id_map:
                continue
            label = edge.get("label")
            if label:
                lines.append(
                    f'    {id_map[from_id]} -->|"{_escape_label(str(label))}"| {id_map[to_id]}'
                )
            else:
                lines.append(f"    {id_map[from_id]} --> {id_map[to_id]}")

        highlights = {node.get("highlight") for node in nodes if isinstance(node, dict)}
        if highlights & {"asis", "tobe", "changed", "removed"}:
            lines.append("    classDef highlight_asis fill:#fef3c7,stroke:#d97706")
            lines.append("    classDef highlight_tobe fill:#dbeafe,stroke:#2563eb")
            lines.append("    classDef highlight_changed fill:#fce7f3,stroke:#db2777")
            lines.append("    classDef highlight_removed fill:#f3f4f6,stroke:#9ca3af,stroke-dasharray:4")

        return "\n".join(lines)
