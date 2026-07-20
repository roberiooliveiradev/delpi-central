from __future__ import annotations

import re
from typing import Any

FLOWCHART_FORMAT = "flowchart_v1"
OVERLAY_FORMAT = "flowchart_overlay_v1"
FORMAT_VERSION = 1

MAX_NODES = 200
MAX_EDGES = 400
MAX_EXTRA_NODES = 50
MAX_EXTRA_EDGES = 100

from tm_app.domain.diagram.bpmn_node_catalog import EDGE_KINDS, NODE_TYPES

MAX_LANES = 12
MAX_LANE_HEIGHT = 400

EDGE_ROUTINGS = frozenset({"straight", "step", "smoothstep"})

NODE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
LANE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class FlowchartValidationError(ValueError):
    pass


def empty_flowchart() -> dict[str, Any]:
    return {
        "format": FLOWCHART_FORMAT,
        "format_version": FORMAT_VERSION,
        "nodes": [],
        "edges": [],
    }


def empty_overlay() -> dict[str, Any]:
    return {
        "format": OVERLAY_FORMAT,
        "format_version": FORMAT_VERSION,
        "modo": "full_scope",
        "node_overrides": {},
        "edge_overrides": {},
        "removed_node_ids": [],
        "removed_edge_ids": [],
        "extra_nodes": [],
        "extra_edges": [],
    }


def empty_escopo() -> dict[str, Any]:
    return {
        "node_ids": [],
        "inherit_all": True,
        "include_boundary_edges": False,
    }


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FlowchartValidationError(f"{label} deve ser um objeto.")
    return value


def _validate_node(node: Any, *, index: int) -> None:
    if not isinstance(node, dict):
        raise FlowchartValidationError(f"nodes[{index}] deve ser um objeto.")
    node_id = node.get("id")
    if not isinstance(node_id, str) or not NODE_ID_PATTERN.match(node_id):
        raise FlowchartValidationError(f"nodes[{index}].id inválido.")
    node_type = node.get("type")
    if node_type not in NODE_TYPES:
        raise FlowchartValidationError(f"nodes[{index}].type inválido: {node_type!r}.")
    label = node.get("label")
    if not isinstance(label, str) or not label.strip():
        raise FlowchartValidationError(f"nodes[{index}].label obrigatório.")
    position = node.get("position")
    if not isinstance(position, dict):
        raise FlowchartValidationError(f"nodes[{index}].position obrigatório.")
    if not isinstance(position.get("x"), (int, float)):
        raise FlowchartValidationError(f"nodes[{index}].position.x inválido.")
    if not isinstance(position.get("y"), (int, float)):
        raise FlowchartValidationError(f"nodes[{index}].position.y inválido.")


def _validate_edge(edge: Any, *, index: int, node_ids: set[str] | None) -> None:
    if not isinstance(edge, dict):
        raise FlowchartValidationError(f"edges[{index}] deve ser um objeto.")
    edge_id = edge.get("id")
    if not isinstance(edge_id, str) or not edge_id.strip():
        raise FlowchartValidationError(f"edges[{index}].id obrigatório.")
    from_id = edge.get("from")
    to_id = edge.get("to")
    if not isinstance(from_id, str) or not from_id.strip():
        raise FlowchartValidationError(f"edges[{index}].from inválido.")
    if not isinstance(to_id, str) or not to_id.strip():
        raise FlowchartValidationError(f"edges[{index}].to inválido.")
    if node_ids is not None:
        if from_id not in node_ids:
            raise FlowchartValidationError(f"edges[{index}].from inválido.")
        if to_id not in node_ids:
            raise FlowchartValidationError(f"edges[{index}].to inválido.")
    label = edge.get("label")
    if label is not None and not isinstance(label, str):
        raise FlowchartValidationError(f"edges[{index}].label inválido.")
    routing = edge.get("routing", "smoothstep")
    if routing is not None and routing not in EDGE_ROUTINGS:
        raise FlowchartValidationError(f"edges[{index}].routing inválido.")
    kind = edge.get("kind", "sequence")
    if kind is not None and kind not in EDGE_KINDS:
        raise FlowchartValidationError(f"edges[{index}].kind inválido.")


def _validate_lane(lane: Any, *, index: int) -> None:
    if not isinstance(lane, dict):
        raise FlowchartValidationError(f"lanes[{index}] deve ser um objeto.")
    lane_id = lane.get("id")
    if not isinstance(lane_id, str) or not LANE_ID_PATTERN.match(lane_id):
        raise FlowchartValidationError(f"lanes[{index}].id inválido.")
    label = lane.get("label")
    if not isinstance(label, str) or not label.strip():
        raise FlowchartValidationError(f"lanes[{index}].label obrigatório.")
    height = lane.get("height")
    if height is not None and (not isinstance(height, (int, float)) or height <= 0):
        raise FlowchartValidationError(f"lanes[{index}].height inválido.")
    if height is not None and float(height) > MAX_LANE_HEIGHT:
        raise FlowchartValidationError(f"lanes[{index}].height acima do limite.")


def validate_flowchart_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "diagrama")
    if data.get("format") != FLOWCHART_FORMAT:
        raise FlowchartValidationError("format deve ser flowchart_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise FlowchartValidationError("format_version inválida.")

    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list):
        raise FlowchartValidationError("nodes deve ser uma lista.")
    if not isinstance(edges, list):
        raise FlowchartValidationError("edges deve ser uma lista.")
    if len(nodes) > MAX_NODES:
        raise FlowchartValidationError(f"Máximo de {MAX_NODES} nós.")
    if len(edges) > MAX_EDGES:
        raise FlowchartValidationError(f"Máximo de {MAX_EDGES} arestas.")

    lanes = data.get("lanes", [])
    if lanes is None:
        lanes = []
    if not isinstance(lanes, list):
        raise FlowchartValidationError("lanes deve ser uma lista.")
    if len(lanes) > MAX_LANES:
        raise FlowchartValidationError(f"Máximo de {MAX_LANES} faixas (swimlanes).")

    lane_ids: set[str] = set()
    for index, lane in enumerate(lanes):
        _validate_lane(lane, index=index)
        lane_id = str(lane["id"])
        if lane_id in lane_ids:
            raise FlowchartValidationError(f"lane id duplicado: {lane_id}.")
        lane_ids.add(lane_id)

    seen_ids: set[str] = set()
    for index, node in enumerate(nodes):
        _validate_node(node, index=index)
        node_id = str(node["id"])
        if node_id in seen_ids:
            raise FlowchartValidationError(f"node_id duplicado: {node_id}.")
        seen_ids.add(node_id)
        lane_id = node.get("lane_id")
        if lane_id is not None:
            if not isinstance(lane_id, str) or lane_id not in lane_ids:
                raise FlowchartValidationError(
                    f"nodes[{index}].lane_id inválido ou faixa inexistente."
                )

    seen_edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        _validate_edge(edge, index=index, node_ids=seen_ids)
        edge_id = str(edge["id"])
        if edge_id in seen_edge_ids:
            raise FlowchartValidationError(f"edge id duplicado: {edge_id}.")
        seen_edge_ids.add(edge_id)

    return data


def validate_overlay_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "overlay")
    if data.get("format") != OVERLAY_FORMAT:
        raise FlowchartValidationError("format deve ser flowchart_overlay_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise FlowchartValidationError("format_version inválida.")

    modo = data.get("modo", "full_scope")
    if modo not in {"full_scope", "partial"}:
        raise FlowchartValidationError("modo inválido.")

    node_overrides = data.get("node_overrides", {})
    edge_overrides = data.get("edge_overrides", {})
    if not isinstance(node_overrides, dict):
        raise FlowchartValidationError("node_overrides deve ser objeto.")
    if not isinstance(edge_overrides, dict):
        raise FlowchartValidationError("edge_overrides deve ser objeto.")

    removed_nodes = data.get("removed_node_ids", [])
    removed_edges = data.get("removed_edge_ids", [])
    if not isinstance(removed_nodes, list) or not all(isinstance(x, str) for x in removed_nodes):
        raise FlowchartValidationError("removed_node_ids inválido.")
    if not isinstance(removed_edges, list) or not all(isinstance(x, str) for x in removed_edges):
        raise FlowchartValidationError("removed_edge_ids inválido.")

    extra_nodes = data.get("extra_nodes", [])
    extra_edges = data.get("extra_edges", [])
    if not isinstance(extra_nodes, list):
        raise FlowchartValidationError("extra_nodes inválido.")
    if not isinstance(extra_edges, list):
        raise FlowchartValidationError("extra_edges inválido.")
    if len(extra_nodes) > MAX_EXTRA_NODES:
        raise FlowchartValidationError(f"Máximo de {MAX_EXTRA_NODES} extra_nodes.")
    if len(extra_edges) > MAX_EXTRA_EDGES:
        raise FlowchartValidationError(f"Máximo de {MAX_EXTRA_EDGES} extra_edges.")

    extra_node_ids: set[str] = set()
    for index, node in enumerate(extra_nodes):
        _validate_node(node, index=index)
        node_id = str(node["id"])
        if node_id in extra_node_ids:
            raise FlowchartValidationError(f"extra_nodes id duplicado: {node_id}.")
        extra_node_ids.add(node_id)

    # Endpoints podem apontar para nós do macro (validados no merge/composição).
    for index, edge in enumerate(extra_edges):
        _validate_edge(edge, index=index, node_ids=None)

    lanes = data.get("lanes")
    if lanes is not None:
        if not isinstance(lanes, list):
            raise FlowchartValidationError("lanes inválido.")
        if len(lanes) > MAX_LANES:
            raise FlowchartValidationError(f"Máximo de {MAX_LANES} lanes.")
        seen_lane_ids: set[str] = set()
        for index, lane in enumerate(lanes):
            _validate_lane(lane, index=index)
            lane_id = str(lane["id"])
            if lane_id in seen_lane_ids:
                raise FlowchartValidationError(f"lanes id duplicado: {lane_id}.")
            seen_lane_ids.add(lane_id)

    return data


def validate_escopo(doc: Any, *, macro_node_ids: set[str] | None = None) -> dict[str, Any]:
    data = _require_dict(doc, "escopo")
    node_ids = data.get("node_ids", [])
    if not isinstance(node_ids, list) or not all(isinstance(x, str) for x in node_ids):
        raise FlowchartValidationError("node_ids inválido.")
    inherit_all = data.get("inherit_all", True)
    if not isinstance(inherit_all, bool):
        raise FlowchartValidationError("inherit_all inválido.")
    include_boundary = data.get("include_boundary_edges", False)
    if not isinstance(include_boundary, bool):
        raise FlowchartValidationError("include_boundary_edges inválido.")

    if macro_node_ids is not None and not inherit_all:
        invalid = [node_id for node_id in node_ids if node_id not in macro_node_ids]
        if invalid:
            raise FlowchartValidationError(
                f"node_ids fora do macro: {', '.join(invalid[:5])}."
            )

    return {
        "node_ids": list(node_ids),
        "inherit_all": inherit_all,
        "include_boundary_edges": include_boundary,
    }


def macro_node_ids(macro: dict[str, Any]) -> set[str]:
    return {
        str(node["id"])
        for node in macro.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
