"""G8 — Legacy flowchart_v1 → Transformômetro-native BPMN migration mapper.

Pure domain module: no DB, no HTTP, no TÉO, no frontend.

Input:  normalized composed legacy flowchart (flowchart_v1 dict).
Output: ``MigrationCandidate`` — bpmn_xml (with BPMN-DI), per-object
        classification report, losses, ambiguities, warnings, statistics
        and a stable legacy_id → bpmn_element_id map.

Design contract (G8 spec):
- Every legacy object is classified EXACT | HEURISTIC | AMBIGUOUS |
  UNMAPPABLE | IGNORED_METADATA — nothing is silently mapped.
- Ambiguities carry options and a recommended option; they are resolved
  externally (resolutions dict) and re-prepared — never guessed.
- No vendor-specific extension elements are emitted; legacy metadata is
  reported as IGNORED_METADATA, not smuggled into the artifact.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from xml.dom import minidom

from tm_app.domain.diagram.bpmn_node_catalog import (
    NON_FLOW_NODE_TYPES,
    START_EVENT_TYPES,
    END_EVENT_TYPES,
    catalog_spec,
    normalize_node_type,
)
from tm_app.domain.diagram.flowchart_v1 import validate_flowchart_v1

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"

MIGRATION_FORMAT_VERSION = "g8-migration-v1"

# Default DI geometry per BPMN shape class (bpmn-js-like defaults).
_SHAPE_SIZES: dict[str, tuple[int, int]] = {
    "event_start": (36, 36),
    "event_intermediate_catch": (36, 36),
    "event_intermediate_throw": (36, 36),
    "event_end": (36, 36),
    "boundary": (36, 36),
    "gateway": (50, 50),
    "task": (100, 80),
    "activity_subprocess": (100, 80),
    "activity_call": (100, 80),
    "activity_ad_hoc": (100, 80),
    "activity_transaction": (100, 80),
    "activity_event_subprocess": (100, 80),
    "artifact_document": (50, 50),
    "artifact_data_object": (36, 50),
    "artifact_data_store": (50, 50),
    "artifact_comment": (100, 30),
    "artifact_group": (300, 150),
}
_LANE_HEIGHT = 160
_LANE_WIDTH_MIN = 360
_LANE_PAD = 30

CLASS_EXACT = "EXACT"
CLASS_HEURISTIC = "HEURISTIC"
CLASS_AMBIGUOUS = "AMBIGUOUS"
CLASS_UNMAPPABLE = "UNMAPPABLE"
CLASS_IGNORED_METADATA = "IGNORED_METADATA"

STATUS_READY = "READY"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_BLOCKED = "BLOCKED"

LOSS_NON_BLOCKING = "NON_BLOCKING"
LOSS_BLOCKING = "BLOCKING"

CONF_MEDIUM = "MEDIUM"
CONF_LOW = "LOW"


@dataclass(frozen=True)
class MigrationAmbiguity:
    ambiguity_id: str
    legacy_object_ids: list[str]
    description: str
    options: list[dict[str, Any]]  # [{"id", "label", "requires_values"?}]
    recommended_option: str | None
    confidence: str
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ambiguity_id": self.ambiguity_id,
            "legacy_object_ids": list(self.legacy_object_ids),
            "description": self.description,
            "options": list(self.options),
            "recommended_option": self.recommended_option,
            "confidence": self.confidence,
            "blocking": self.blocking,
        }


@dataclass(frozen=True)
class MigrationLoss:
    loss_id: str
    legacy_object_ids: list[str]
    classification: str  # NON_BLOCKING | BLOCKING
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "loss_id": self.loss_id,
            "legacy_object_ids": list(self.legacy_object_ids),
            "classification": self.classification,
            "description": self.description,
        }


@dataclass
class MigrationCandidate:
    status: str
    bpmn_xml: str
    checksum_sha256: str
    mapping_report: list[dict[str, Any]]
    losses: list[MigrationLoss]
    ambiguities: list[MigrationAmbiguity]
    warnings: list[str]
    statistics: dict[str, Any]
    id_map: dict[str, str]
    source_format: str = MIGRATION_FORMAT_VERSION

    def to_report_dict(self) -> dict[str, Any]:
        """User-facing report — XML intentionally not inlined."""
        return {
            "status": self.status,
            "candidate_sha256": self.checksum_sha256,
            "mapping_report": list(self.mapping_report),
            "losses": [loss.to_dict() for loss in self.losses],
            "ambiguities": [a.to_dict() for a in self.ambiguities],
            "warnings": list(self.warnings),
            "statistics": dict(self.statistics),
            "source_format": self.source_format,
        }


def _sanitize_xml_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(value))
    if not cleaned:
        return "Element_1"
    if cleaned[0].isdigit():
        return f"Id_{cleaned}"
    return cleaned


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _center(node: dict[str, Any], size: tuple[int, int]) -> tuple[float, float]:
    pos = node.get("position") or {}
    return (float(pos.get("x", 0)) + size[0] / 2, float(pos.get("y", 0)) + size[1] / 2)


class LegacyFlowchartToBpmnMapper:
    """Pure mapper: composed flowchart_v1 → MigrationCandidate."""

    def map(
        self,
        flowchart: dict[str, Any],
        *,
        process_name: str = "Processo",
        resolutions: dict[str, Any] | None = None,
    ) -> MigrationCandidate:
        doc = validate_flowchart_v1(flowchart)
        resolutions = dict(resolutions or {})
        report: list[dict[str, Any]] = []
        losses: list[MigrationLoss] = []
        ambiguities: list[MigrationAmbiguity] = []
        warnings: list[str] = []
        id_map: dict[str, str] = {}
        counter = {"n": 0}

        def seq_id() -> str:
            counter["n"] += 1
            return f"M-{counter['n']:03d}"

        nodes = [n for n in doc.get("nodes") or [] if isinstance(n, dict)]
        edges = [e for e in doc.get("edges") or [] if isinstance(e, dict)]
        lanes = [l for l in doc.get("lanes") or [] if isinstance(l, dict)]
        node_by_id = {str(n["id"]): n for n in nodes}
        flow_node_ids = {
            str(n["id"])
            for n in nodes
            if normalize_node_type(str(n.get("type") or "process"))
            not in NON_FLOW_NODE_TYPES
        }

        # ---- element plan ------------------------------------------------
        for node in nodes:
            legacy_id = str(node["id"])
            node_type = normalize_node_type(str(node.get("type") or "process"))
            spec = catalog_spec(node_type)
            bpmn_id = _sanitize_xml_id(legacy_id)
            if bpmn_id in id_map.values():
                bpmn_id = _sanitize_xml_id(f"{legacy_id}_el")
            id_map[legacy_id] = bpmn_id
            node["_bpmn_id"] = bpmn_id
            node["_bpmn_tag"] = spec.get("bpmn_tag", "task")
            node["_bpmn_event_def"] = spec.get("bpmn_event_definition")
            node["_bpmn_shape"] = spec.get("shape", "task")
            node["_bpmn_flow"] = spec.get("participates_in_flow", True)
            node["_bpmn_type"] = node_type

        # ---- nodes --------------------------------------------------------
        activity_ids = [
            str(n["id"])
            for n in nodes
            if n.get("_bpmn_tag")
            in {
                "task",
                "userTask",
                "serviceTask",
                "manualTask",
                "scriptTask",
                "businessRuleTask",
                "sendTask",
                "receiveTask",
                "subProcess",
                "callActivity",
                "adHocSubProcess",
                "transaction",
            }
        ]

        unresolved_ambiguity = False
        for node in nodes:
            legacy_id = str(node["id"])
            node_type = node["_bpmn_type"]
            notes: list[str] = []
            classification = CLASS_EXACT

            if node_type.startswith("boundary_"):
                attached = self._resolve_boundary_attachment(
                    node, nodes, activity_ids, resolutions, ambiguities
                )
                if attached == "__ambiguous__":
                    classification = CLASS_AMBIGUOUS
                    unresolved_ambiguity = True
                elif attached:
                    node["_attached_to"] = attached
                    classification = CLASS_HEURISTIC
                    notes.append("attachedToRef inferido pela geometria legada.")
                else:
                    node["_bpmn_tag"] = "intermediateCatchEvent"
                    node["_bpmn_event_def"] = "timerEventDefinition"
                    node["_bpmn_shape"] = "event_intermediate_catch"
                    classification = CLASS_HEURISTIC
                    notes.append(
                        "Convertido em intermediateCatchEvent (sem alvo de anexo)."
                    )

            report.append(
                {
                    "mapping_id": seq_id(),
                    "legacy_id": legacy_id,
                    "legacy_kind": "node",
                    "legacy_type": str(node.get("type")),
                    "target_element_id": node["_bpmn_id"],
                    "target_bpmn_tag": node["_bpmn_tag"],
                    "classification": classification,
                    "notes": notes,
                }
            )

            if node.get("highlight"):
                report.append(
                    {
                        "mapping_id": seq_id(),
                        "legacy_id": legacy_id,
                        "legacy_kind": "node.highlight",
                        "classification": CLASS_IGNORED_METADATA,
                        "notes": ["highlight não existe em BPMN; preservado no legado."],
                    }
                )
            if isinstance(node.get("meta"), dict) and node["meta"]:
                report.append(
                    {
                        "mapping_id": seq_id(),
                        "legacy_id": legacy_id,
                        "legacy_kind": "node.meta",
                        "classification": CLASS_IGNORED_METADATA,
                        "notes": ["meta não é serializado no BPMN canônico."],
                    }
                )

        # ---- lanes ---------------------------------------------------------
        lane_ids: set[str] = set()
        for lane in lanes:
            legacy_id = str(lane.get("id") or "lane")
            bpmn_id = _sanitize_xml_id(legacy_id)
            if bpmn_id in lane_ids:
                bpmn_id = _sanitize_xml_id(f"{legacy_id}_lane")
            lane_ids.add(bpmn_id)
            lane["_bpmn_id"] = bpmn_id
            id_map[f"lane:{legacy_id}"] = bpmn_id
            report.append(
                {
                    "mapping_id": seq_id(),
                    "legacy_id": legacy_id,
                    "legacy_kind": "lane",
                    "target_element_id": bpmn_id,
                    "target_bpmn_tag": "lane",
                    "classification": CLASS_EXACT,
                    "notes": [],
                }
            )

        # ---- edges ----------------------------------------------------------
        outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in edges:
            outgoing.setdefault(str(edge.get("from") or ""), []).append(edge)

        decision_nodes = {
            nid
            for nid, n in node_by_id.items()
            if n.get("_bpmn_tag") in {"exclusiveGateway", "inclusiveGateway"}
        }

        for edge in edges:
            legacy_id = str(
                edge.get("id") or f"{edge.get('from')}_{edge.get('to')}"
            )
            kind = str(edge.get("kind") or "sequence")
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            from_flow = from_id in flow_node_ids
            to_flow = to_id in flow_node_ids
            classification = CLASS_EXACT
            notes: list[str] = []
            bpmn_tag = "sequenceFlow"
            skip = False

            if kind == "association":
                bpmn_tag = "association"
            elif kind == "sequence" and not (from_flow and to_flow):
                bpmn_tag = "association"
                classification = CLASS_HEURISTIC
                notes.append("Endpoint não é flow node; sequenceFlow → association.")
            elif kind == "message_flow":
                resolved_tag = self._resolve_message_flow(
                    edge, from_flow and to_flow, resolutions, ambiguities
                )
                if resolved_tag == "__ambiguous__":
                    classification = CLASS_AMBIGUOUS
                    unresolved_ambiguity = True
                    bpmn_tag = "sequenceFlow"  # provisional render
                    notes.append("messageFlow requer participants; render provisório.")
                elif resolved_tag == "__drop__":
                    skip = True
                    bpmn_tag = "sequenceFlow"
                    losses.append(
                        MigrationLoss(
                            loss_id=f"L-{legacy_id}",
                            legacy_object_ids=[legacy_id],
                            classification=LOSS_NON_BLOCKING,
                            description="message_flow descartado por resolução humana.",
                        )
                    )
                else:
                    bpmn_tag = resolved_tag
                    classification = CLASS_HEURISTIC
                    notes.append("message_flow resolvido como sequenceFlow.")

            if kind == "sequence" and edge.get("routing"):
                report.append(
                    {
                        "mapping_id": seq_id(),
                        "legacy_id": legacy_id,
                        "legacy_kind": "edge.routing",
                        "classification": CLASS_IGNORED_METADATA,
                        "notes": ["routing hint não persiste; waypoints derivados."],
                    }
                )

            edge["_bpmn_tag"] = bpmn_tag
            edge["_skip"] = skip
            edge["_bpmn_id"] = _sanitize_xml_id(legacy_id)
            id_map[f"edge:{legacy_id}"] = edge["_bpmn_id"]
            report.append(
                {
                    "mapping_id": seq_id(),
                    "legacy_id": legacy_id,
                    "legacy_kind": "edge",
                    "legacy_type": kind,
                    "target_element_id": edge["_bpmn_id"],
                    "target_bpmn_tag": bpmn_tag,
                    "classification": classification,
                    "notes": notes,
                }
            )

        # ---- gateway decisions without conditions ----------------------------
        for gw_id in sorted(decision_nodes):
            outs = [
                e
                for e in outgoing.get(gw_id, [])
                if e.get("_bpmn_tag") == "sequenceFlow" and not e.get("_skip")
            ]
            if len(outs) <= 1:
                continue
            unlabeled = [
                e for e in outs if not str(e.get("label") or "").strip()
            ]
            if not unlabeled:
                continue
            amb_id = f"A-gw-{gw_id}"
            resolution = resolutions.get(amb_id)
            if isinstance(resolution, dict):
                opt = resolution.get("option")
                if opt == "accept_unconditional":
                    continue
                if opt == "label_edges":
                    values = resolution.get("values") or {}
                    for e in unlabeled:
                        lbl = str(values.get(str(e.get("id")) or "") or "").strip()
                        if lbl:
                            e["label"] = lbl
                    if not [
                        e for e in outs if not str(e.get("label") or "").strip()
                    ]:
                        continue
            unlabeled_ids = [
                str(e.get("id") or f"{e.get('from')}_{e.get('to')}")
                for e in unlabeled
            ]
            ambiguities.append(
                MigrationAmbiguity(
                    ambiguity_id=amb_id,
                    legacy_object_ids=[gw_id, *unlabeled_ids],
                    description=(
                        f"Gateway '{node_by_id[gw_id].get('label') or gw_id}' possui "
                        f"{len(unlabeled)} saída(s) sem condição/label explícita."
                    ),
                    options=[
                        {
                            "id": "label_edges",
                            "label": "Definir condições (labels) nas saídas",
                            "requires_values": True,
                        },
                        {
                            "id": "accept_unconditional",
                            "label": "Manter saídas incondicionais (semântica BPMN válida)",
                        },
                    ],
                    recommended_option="label_edges",
                    confidence=CONF_MEDIUM,
                )
            )
            unresolved_ambiguity = True

        # ---- structural warnings ----------------------------------------------
        start_nodes = [n for n in nodes if n["_bpmn_type"] in START_EVENT_TYPES]
        end_nodes = [n for n in nodes if n["_bpmn_type"] in END_EVENT_TYPES]
        if not start_nodes:
            warnings.append(
                "Nenhum start event explícito — BPMN permite início implícito, "
                "mas recomenda-se revisão."
            )
        if not end_nodes:
            warnings.append(
                "Nenhum end event explícito — o processo pode não ter término claro."
            )
        has_outgoing = {str(e.get("from")) for e in edges}
        has_incoming = {str(e.get("to")) for e in edges}
        for node in nodes:
            nid = str(node["id"])
            if node["_bpmn_type"] in START_EVENT_TYPES | END_EVENT_TYPES:
                continue
            if nid not in has_outgoing and nid not in has_incoming:
                warnings.append(
                    f"Nó '{node.get('label') or nid}' isolado (sem conexões)."
                )

        # ---- XML + DI emission --------------------------------------------------
        bpmn_xml = self._emit_xml(nodes, edges, lanes, process_name=process_name,
                                  id_map=id_map)
        checksum = hashlib.sha256(bpmn_xml.encode("utf-8")).hexdigest()

        blocking_losses = [l for l in losses if l.classification == LOSS_BLOCKING]
        if blocking_losses:
            status = STATUS_BLOCKED
        elif unresolved_ambiguity:
            status = STATUS_AMBIGUOUS
        else:
            status = STATUS_READY

        counts: dict[str, int] = {}
        for item in report:
            counts[item["classification"]] = counts.get(item["classification"], 0) + 1

        statistics = {
            "legacy_nodes": len(nodes),
            "legacy_edges": len(edges),
            "legacy_lanes": len(lanes),
            "by_classification": counts,
            "unresolved_ambiguities": len(ambiguities),
            "warnings": len(warnings),
        }

        return MigrationCandidate(
            status=status,
            bpmn_xml=bpmn_xml,
            checksum_sha256=checksum,
            mapping_report=report,
            losses=losses,
            ambiguities=ambiguities,
            warnings=warnings,
            statistics=statistics,
            id_map=id_map,
        )

    # ------------------------------------------------------------------
    def _resolve_boundary_attachment(
        self,
        node: dict[str, Any],
        nodes: list[dict[str, Any]],
        activity_ids: list[str],
        resolutions: dict[str, Any],
        ambiguities: list[MigrationAmbiguity],
    ) -> str | None:
        amb_id = f"A-boundary-{node['id']}"
        resolution = resolutions.get(amb_id)
        if isinstance(resolution, dict):
            opt = resolution.get("option")
            if opt == "convert_to_intermediate":
                return None
            if opt == "attach_to":
                target = str(
                    (resolution.get("values") or {}).get("activity_id") or ""
                )
                if target in activity_ids:
                    return target
        # Geometry inference: activity whose padded bounds contain the node.
        pos = node.get("position") or {}
        cx, cy = float(pos.get("x", 0)), float(pos.get("y", 0))
        candidates = []
        for aid in activity_ids:
            target = next(n for n in nodes if str(n["id"]) == aid)
            tpos = target.get("position") or {}
            tx, ty = float(tpos.get("x", 0)), float(tpos.get("y", 0))
            w, h = _SHAPE_SIZES.get(target.get("_bpmn_shape", "task"), (100, 80))
            if tx - 20 <= cx <= tx + w + 20 and ty - 20 <= cy <= ty + h + 20:
                candidates.append(aid)
        if len(candidates) == 1:
            return candidates[0]
        ambiguities.append(
            MigrationAmbiguity(
                ambiguity_id=amb_id,
                legacy_object_ids=[str(node["id"])],
                description=(
                    f"Boundary event '{node.get('label') or node['id']}' sem alvo de "
                    f"anexação determinístico ({len(candidates)} candidatos)."
                ),
                options=[
                    {
                        "id": "attach_to",
                        "label": "Anexar a atividade",
                        "requires_values": True,
                    },
                    {
                        "id": "convert_to_intermediate",
                        "label": "Converter em evento intermediário",
                    },
                ],
                recommended_option="attach_to" if candidates else "convert_to_intermediate",
                confidence=CONF_LOW if not candidates else CONF_MEDIUM,
            )
        )
        return "__ambiguous__"

    def _resolve_message_flow(
        self,
        edge: dict[str, Any],
        both_flow: bool,
        resolutions: dict[str, Any],
        ambiguities: list[MigrationAmbiguity],
    ) -> str:
        edge_id = str(edge.get("id") or f"{edge.get('from')}_{edge.get('to')}")
        amb_id = f"A-mf-{edge_id}"
        resolution = resolutions.get(amb_id)
        if isinstance(resolution, dict):
            opt = resolution.get("option")
            if opt == "as_sequence" and both_flow:
                return "sequenceFlow"
            if opt == "drop":
                return "__drop__"
        ambiguities.append(
            MigrationAmbiguity(
                ambiguity_id=amb_id,
                legacy_object_ids=[edge_id],
                description=(
                    f"Edge '{edge_id}' é message_flow; legado não possui "
                    f"participants/pools para messageFlow BPMN válido."
                ),
                options=[
                    {"id": "as_sequence", "label": "Mapear como sequenceFlow"},
                    {"id": "drop", "label": "Descartar aresta"},
                ],
                recommended_option="as_sequence" if both_flow else "drop",
                confidence=CONF_MEDIUM,
            )
        )
        return "__ambiguous__"

    # ------------------------------------------------------------------
    def _emit_xml(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        lanes: list[dict[str, Any]],
        *,
        process_name: str,
        id_map: dict[str, str],
    ) -> str:
        ET.register_namespace("bpmn", BPMN_NS)
        ET.register_namespace("bpmndi", BPMNDI_NS)
        ET.register_namespace("dc", DC_NS)
        ET.register_namespace("di", DI_NS)

        root = ET.Element(
            f"{{{BPMN_NS}}}definitions",
            attrib={
                "id": "Definitions_1",
                "targetNamespace": "http://delpi.local/bpmn/migrated",
            },
        )
        process_el = ET.SubElement(
            root,
            f"{{{BPMN_NS}}}process",
            attrib={
                "id": "Process_1",
                "name": _esc(process_name),
                "isExecutable": "false",
            },
        )

        if lanes:
            lane_set_el = ET.SubElement(
                process_el, f"{{{BPMN_NS}}}laneSet", attrib={"id": "LaneSet_1"}
            )
            lane_el_by_id: dict[str, ET.Element] = {}
            for lane in lanes:
                lane_el = ET.SubElement(
                    lane_set_el,
                    f"{{{BPMN_NS}}}lane",
                    attrib={
                        "id": lane["_bpmn_id"],
                        "name": _esc(str(lane.get("label") or lane["_bpmn_id"])),
                    },
                )
                lane_el_by_id[str(lane.get("id"))] = lane_el
            for node in nodes:
                lref = str(node.get("lane_id") or "")
                if lref and lref in lane_el_by_id:
                    ref = ET.SubElement(
                        lane_el_by_id[lref], f"{{{BPMN_NS}}}flowNodeRef"
                    )
                    ref.text = node["_bpmn_id"]

        for node in nodes:
            tag = node["_bpmn_tag"]
            attrs = {
                "id": node["_bpmn_id"],
                "name": _esc(str(node.get("label") or node["_bpmn_id"])),
            }
            if node.get("_attached_to"):
                attrs["attachedToRef"] = id_map[node["_attached_to"]]
            element = ET.SubElement(process_el, f"{{{BPMN_NS}}}{tag}", attrib=attrs)
            if node.get("_bpmn_event_def"):
                ET.SubElement(element, f"{{{BPMN_NS}}}{node['_bpmn_event_def']}")

        for edge in edges:
            if edge.get("_skip"):
                continue
            tag = edge["_bpmn_tag"]
            attrs = {
                "id": edge["_bpmn_id"],
                "sourceRef": id_map.get(str(edge.get("from") or ""), ""),
                "targetRef": id_map.get(str(edge.get("to") or ""), ""),
            }
            label = edge.get("label")
            if label and tag == "sequenceFlow":
                attrs["name"] = _esc(str(label))
            ET.SubElement(process_el, f"{{{BPMN_NS}}}{tag}", attrib=attrs)

        # ---- BPMN-DI ---------------------------------------------------------
        diagram_el = ET.SubElement(
            root,
            f"{{{BPMNDI_NS}}}BPMNDiagram",
            attrib={"id": "BPMNDiagram_1"},
        )
        plane_el = ET.SubElement(
            diagram_el,
            f"{{{BPMNDI_NS}}}BPMNPlane",
            attrib={"id": "BPMNPlane_1", "bpmnElement": "Process_1"},
        )

        node_el_by_id = {str(n["id"]): n for n in nodes}
        if lanes:
            max_x = max(
                (float((n.get("position") or {}).get("x", 0)) for n in nodes),
                default=300,
            ) + 200
            ordered = sorted(
                lanes,
                key=lambda l: (float(l.get("order", 0) or 0), str(l.get("id"))),
            )
            y = 0.0
            lane_bounds: dict[str, tuple[float, float, float, float]] = {}
            for lane in ordered:
                members = [
                    n
                    for n in nodes
                    if str(n.get("lane_id") or "") == str(lane.get("id"))
                ]
                h = float(lane.get("height") or _LANE_HEIGHT)
                if members:
                    min_y = min(
                        float((m.get("position") or {}).get("y", 0)) for m in members
                    )
                    max_y = max(
                        float((m.get("position") or {}).get("y", 0))
                        + _SHAPE_SIZES.get(m["_bpmn_shape"], (100, 80))[1]
                        for m in members
                    )
                    y = min(y, min_y - _LANE_PAD)
                    h = max(h, (max_y - y) + _LANE_PAD)
                lane_bounds[str(lane.get("id"))] = (
                    0.0,
                    y,
                    max(max_x, _LANE_WIDTH_MIN),
                    h,
                )
                y += h
            for lane in ordered:
                x, yy, w, h = lane_bounds[str(lane.get("id"))]
                shape = ET.SubElement(
                    plane_el,
                    f"{{{BPMNDI_NS}}}BPMNShape",
                    attrib={
                        "id": f"{lane['_bpmn_id']}_di",
                        "bpmnElement": lane["_bpmn_id"],
                        "isHorizontal": "true",
                    },
                )
                ET.SubElement(
                    shape,
                    f"{{{DC_NS}}}Bounds",
                    attrib={
                        "x": f"{x:.0f}",
                        "y": f"{yy:.0f}",
                        "width": f"{w:.0f}",
                        "height": f"{h:.0f}",
                    },
                )

        for node in nodes:
            pos = node.get("position") or {}
            w, h = _SHAPE_SIZES.get(node["_bpmn_shape"], (100, 80))
            shape = ET.SubElement(
                plane_el,
                f"{{{BPMNDI_NS}}}BPMNShape",
                attrib={
                    "id": f"{node['_bpmn_id']}_di",
                    "bpmnElement": node["_bpmn_id"],
                },
            )
            ET.SubElement(
                shape,
                f"{{{DC_NS}}}Bounds",
                attrib={
                    "x": f"{float(pos.get('x', 0)):.0f}",
                    "y": f"{float(pos.get('y', 0)):.0f}",
                    "width": f"{w}",
                    "height": f"{h}",
                },
            )

        for edge in edges:
            if edge.get("_skip"):
                continue
            src = node_el_by_id.get(str(edge.get("from") or ""))
            dst = node_el_by_id.get(str(edge.get("to") or ""))
            if src is None or dst is None:
                continue
            di_el = ET.SubElement(
                plane_el,
                f"{{{BPMNDI_NS}}}BPMNEdge",
                attrib={
                    "id": f"{edge['_bpmn_id']}_di",
                    "bpmnElement": edge["_bpmn_id"],
                },
            )
            sw, sh = _SHAPE_SIZES.get(src["_bpmn_shape"], (100, 80))
            dw, dh = _SHAPE_SIZES.get(dst["_bpmn_shape"], (100, 80))
            sx, sy = _center(src, (sw, sh))
            dx, dy = _center(dst, (dw, dh))
            ET.SubElement(
                di_el,
                f"{{{DI_NS}}}waypoint",
                attrib={"x": f"{sx:.0f}", "y": f"{sy:.0f}"},
            )
            ET.SubElement(
                di_el,
                f"{{{DI_NS}}}waypoint",
                attrib={"x": f"{dx:.0f}", "y": f"{dy:.0f}"},
            )

        rough = ET.tostring(root, encoding="unicode")
        return minidom.parseString(rough).toprettyxml(indent="  ")
