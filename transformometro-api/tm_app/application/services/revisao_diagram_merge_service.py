from __future__ import annotations

import copy
from typing import Any

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService
from tm_app.domain.diagram.flowchart_v1 import (
    empty_escopo,
    empty_flowchart,
    empty_overlay,
    macro_node_ids,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)


class RevisaoDiagramMergeService:
    def __init__(self, mermaid_exporter: DiagramMermaidExportService | None = None) -> None:
        self._mermaid = mermaid_exporter or DiagramMermaidExportService()

    def merge(
        self,
        *,
        macro: dict[str, Any] | None,
        escopo: dict[str, Any] | None,
        overlay: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = copy.deepcopy(validate_flowchart_v1(macro or empty_flowchart()))
        scope = validate_escopo(escopo or empty_escopo(), macro_node_ids=macro_node_ids(base))
        overlay_doc = validate_overlay_v1(overlay or empty_overlay())

        scoped = self._apply_scope(base, scope)
        merged = self._apply_overlay(scoped, overlay_doc)
        warnings = self._collect_warnings(base, scope, overlay_doc)

        mermaid = self._mermaid.flowchart_to_mermaid(merged)
        return {
            "flowchart": merged,
            "mermaid": mermaid,
            "warnings": warnings,
            "escopo": scope,
            "overlay": overlay_doc,
        }

    @staticmethod
    def overlay_is_empty(overlay: dict[str, Any] | None) -> bool:
        doc = validate_overlay_v1(overlay or empty_overlay())
        return (
            not (doc.get("node_overrides") or {})
            and not (doc.get("edge_overrides") or {})
            and not (doc.get("removed_node_ids") or [])
            and not (doc.get("removed_edge_ids") or [])
            and not (doc.get("extra_nodes") or [])
            and not (doc.get("extra_edges") or [])
            and "lanes" not in doc
        )

    def build_revisao_view(
        self,
        *,
        macro: dict[str, Any] | None,
        escopo: dict[str, Any] | None,
        overlay: dict[str, Any] | None,
        reference_overlay: dict[str, Any] | None = None,
        reference_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Visão de edição da revisão (PB19 S7 / espelho PB23).

        - flowchart_base: macro ∩ escopo (persistência absoluta do overlay).
        - flowchart_reference: merge da revisão de referência.
        - flowchart: overlay próprio; se vazio e há referência, seed na referência.
        """
        own = self.merge(macro=macro, escopo=escopo, overlay=overlay)
        flowchart_base = self._apply_scope(
            copy.deepcopy(validate_flowchart_v1(macro or empty_flowchart())),
            own["escopo"],
        )

        reference_flowchart = None
        referencia = None
        if reference_meta is not None or reference_overlay is not None:
            ref_merged = self.merge(
                macro=macro,
                escopo=escopo,
                overlay=reference_overlay,
            )
            reference_flowchart = ref_merged["flowchart"]
            if reference_meta:
                referencia = {
                    "revisao_id": reference_meta.get("revisao_id"),
                    "versao_revisao": reference_meta.get("versao_revisao"),
                    "cenario_tipo": reference_meta.get("cenario_tipo"),
                }

        working = own["flowchart"]
        seeded_from_reference = False
        if reference_flowchart is not None and self.overlay_is_empty(overlay):
            working = copy.deepcopy(reference_flowchart)
            seeded_from_reference = True

        reference_diff = None
        if reference_flowchart is not None:
            reference_diff = self.diff_highlights(
                baseline=reference_flowchart,
                current=working,
            )

        mermaid = self._mermaid.flowchart_to_mermaid(working)
        return {
            **own,
            "flowchart": working,
            "flowchart_base": flowchart_base,
            "flowchart_reference": reference_flowchart,
            "mermaid": mermaid,
            "referencia": referencia,
            "seeded_from_reference": seeded_from_reference,
            "baseline_diff": reference_diff,
            "reference_diff": reference_diff,
        }

    def apply_overlay_to_flowchart(
        self,
        flowchart: dict[str, Any],
        overlay: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Aplica overlay sobre um flowchart já validado (composição temporal)."""
        return self._apply_overlay(
            copy.deepcopy(flowchart),
            validate_overlay_v1(overlay or empty_overlay()),
        )

    def diff_highlights(
        self,
        *,
        baseline: dict[str, Any] | None,
        current: dict[str, Any] | None,
    ) -> dict[str, Any]:
        baseline_nodes = {
            str(node["id"]): node
            for node in (baseline or empty_flowchart()).get("nodes", [])
            if isinstance(node, dict) and node.get("id")
        }
        current_nodes = {
            str(node["id"]): node
            for node in (current or empty_flowchart()).get("nodes", [])
            if isinstance(node, dict) and node.get("id")
        }

        changed: list[str] = []
        added: list[str] = []
        removed: list[str] = []

        for node_id, node in current_nodes.items():
            if node_id not in baseline_nodes:
                added.append(node_id)
            elif str(node.get("label")) != str(baseline_nodes[node_id].get("label")):
                changed.append(node_id)

        for node_id in baseline_nodes:
            if node_id not in current_nodes:
                removed.append(node_id)

        return {"changed": changed, "added": added, "removed": removed}

    def _apply_scope(self, macro: dict[str, Any], escopo: dict[str, Any]) -> dict[str, Any]:
        if escopo.get("inherit_all", True):
            return macro

        allowed = set(escopo.get("node_ids") or [])
        if not allowed:
            return {**macro, "nodes": [], "edges": []}

        include_boundary = bool(escopo.get("include_boundary_edges"))
        nodes = [
            node
            for node in macro.get("nodes", [])
            if isinstance(node, dict) and str(node.get("id")) in allowed
        ]
        node_set = {str(node["id"]) for node in nodes}

        edges = []
        for edge in macro.get("edges", []):
            if not isinstance(edge, dict):
                continue
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id in node_set and to_id in node_set:
                edges.append(edge)
            elif include_boundary and (from_id in node_set or to_id in node_set):
                edges.append(edge)

        return {**macro, "nodes": nodes, "edges": edges}

    def _apply_overlay(self, scoped: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(scoped)
        removed_nodes = set(overlay.get("removed_node_ids") or [])
        removed_edges = set(overlay.get("removed_edge_ids") or [])
        node_overrides = overlay.get("node_overrides") or {}
        edge_overrides = overlay.get("edge_overrides") or {}

        nodes = []
        for node in result.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("id") or "")
            if node_id in removed_nodes:
                continue
            merged_node = copy.deepcopy(node)
            override = node_overrides.get(node_id)
            if isinstance(override, dict):
                if override.get("label") is not None:
                    merged_node["label"] = override["label"]
                if override.get("type") in {
                    "start", "end", "process", "decision", "document", "data", "subprocess", "comment"
                }:
                    merged_node["type"] = override["type"]
                if isinstance(override.get("position"), dict):
                    merged_node["position"] = override["position"]
                if "lane_id" in override:
                    lane_id = override.get("lane_id")
                    if lane_id is None or lane_id == "":
                        merged_node.pop("lane_id", None)
                    else:
                        merged_node["lane_id"] = lane_id
                if override.get("highlight"):
                    merged_node["highlight"] = override["highlight"]
                if isinstance(override.get("meta"), dict):
                    merged_node["meta"] = {**(merged_node.get("meta") or {}), **override["meta"]}
            nodes.append(merged_node)

        extra_nodes = overlay.get("extra_nodes") or []
        existing_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict)}
        for node in extra_nodes:
            if isinstance(node, dict) and str(node.get("id")) not in existing_ids:
                nodes.append(copy.deepcopy(node))

        node_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict)}

        edges = []
        for edge in result.get("edges", []):
            if not isinstance(edge, dict):
                continue
            edge_id = str(edge.get("id") or "")
            if edge_id in removed_edges:
                continue
            merged_edge = copy.deepcopy(edge)
            override = edge_overrides.get(edge_id)
            if isinstance(override, dict):
                if override.get("label") is not None:
                    merged_edge["label"] = override["label"]
                if override.get("from"):
                    merged_edge["from"] = override["from"]
                if override.get("to"):
                    merged_edge["to"] = override["to"]
            from_id = str(merged_edge.get("from") or "")
            to_id = str(merged_edge.get("to") or "")
            if from_id in node_ids and to_id in node_ids:
                edges.append(merged_edge)

        for edge in overlay.get("extra_edges") or []:
            if not isinstance(edge, dict):
                continue
            from_id = str(edge.get("from") or "")
            to_id = str(edge.get("to") or "")
            if from_id in node_ids and to_id in node_ids:
                edges.append(copy.deepcopy(edge))

        out = {**result, "nodes": nodes, "edges": edges}
        if "lanes" in overlay and isinstance(overlay.get("lanes"), list):
            out["lanes"] = copy.deepcopy(overlay["lanes"])
        return out

    def _collect_warnings(
        self,
        macro: dict[str, Any],
        escopo: dict[str, Any],
        overlay: dict[str, Any],
    ) -> list[str]:
        warnings: list[str] = []
        ids = macro_node_ids(macro)
        if not escopo.get("inherit_all", True):
            for node_id in escopo.get("node_ids") or []:
                if node_id not in ids:
                    warnings.append(f"Nó {node_id} não existe no macro.")
        for node_id in overlay.get("node_overrides") or {}:
            if node_id not in ids and node_id not in {
                str(node.get("id"))
                for node in overlay.get("extra_nodes") or []
                if isinstance(node, dict)
            }:
                warnings.append(f"Override referencia nó ausente no macro: {node_id}.")
        return warnings
