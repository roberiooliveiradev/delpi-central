"""Playbook 19 S7 — composição temporal do diagrama macro (base + deltas vigentes)."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from typing import Any

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService
from tm_app.application.services.decomposition_composition_service import (
    revisao_vigente_em,
)
from tm_app.application.services.revision_diagram_merge_service import RevisaoDiagramMergeService
from tm_app.domain.diagram.flowchart_v1 import (
    empty_escopo,
    empty_flowchart,
    empty_overlay,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)
from tm_app.infrastructure.persistence.repositories.instance_scope_diagram_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.process_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import RevisaoRepository


def _sort_key_revisao(revisao: dict[str, Any]) -> tuple:
    from datetime import datetime

    raw = revisao.get("data_inicio_vigencia")
    if isinstance(raw, datetime):
        start = raw.date()
    elif isinstance(raw, date):
        start = raw
    else:
        try:
            start = date.fromisoformat(str(raw or "")[:10])
        except ValueError:
            start = date.min
    versao = str(revisao.get("versao_revisao") or "")
    return (start, versao, str(revisao.get("revisao_id") or ""))


_ABSENT_SIG = ("absent",)


def _node_semantic_signature(node: dict[str, Any] | None) -> tuple:
    """Semantic payload of a node — identity-independent equivalence.

    Semantic: type/label/lane_id. Geometry (position) and product metadata
    (highlight/meta) are intentionally excluded from equivalence.
    """
    if not isinstance(node, dict):
        return ("absent",)
    return (
        "present",
        str(node.get("type") or ""),
        str(node.get("label") or ""),
        str(node.get("lane_id") or ""),
    )


def _node_geometry_signature(node: dict[str, Any] | None) -> tuple:
    if not isinstance(node, dict):
        return ("absent",)
    pos = node.get("position") if isinstance(node.get("position"), dict) else {}
    return ("present", pos.get("x"), pos.get("y"))


def _edge_semantic_signature(edge: dict[str, Any] | None) -> tuple:
    """Semantic payload of an edge: from/to/kind/label."""
    if not isinstance(edge, dict):
        return ("absent",)
    return (
        "present",
        str(edge.get("from") or ""),
        str(edge.get("to") or ""),
        str(edge.get("kind") or ""),
        str(edge.get("label") or ""),
    )


def _node_signature(node: dict[str, Any] | None, *, present: bool) -> tuple:
    if not present or node is None:
        return ("absent",)
    return (
        "present",
        str(node.get("label") or ""),
        str(node.get("type") or ""),
        str(node.get("highlight") or ""),
    )


def _edge_state_signature(edge: dict[str, Any] | None) -> tuple:
    """Merged-state signature of an edge (presence + semantic payload)."""
    return _edge_semantic_signature(edge)


def _overlay_content_sha(overlay: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(overlay, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _conflict_entry(
    *,
    object_id: str,
    object_kind: str,
    contributors: list[dict[str, Any]],
    reason: str,
    winner_revisao_id: str | None,
    field: str,
) -> dict[str, Any]:
    """Structured composition conflict (G8-COMP-1)."""
    return {
        "conflict_id": f"cc_{object_kind}_{object_id}",
        "object_id": object_id,
        "object_kind": object_kind,
        # compat keys consumed by the existing composed-section UI
        "node_id": object_id if object_kind == "node" else None,
        "field": field,
        "reason": reason,
        "winner_revisao_id": winner_revisao_id,
        "contributors": contributors,
        "revisoes": [
            {
                "revisao_id": c.get("revisao_id"),
                "instancia_id": c.get("instancia_id"),
                "versao_revisao": c.get("versao_revisao"),
            }
            for c in contributors
        ],
    }


def _reconcile_extras(
    scoped_overlay: dict[str, Any],
    *,
    composed: dict[str, Any],
    contributor: dict[str, Any],
    provenance: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Dedup equivalent same-id extra_nodes/extra_edges; conflict on divergence.

    G8-COMP-1: multiple instances can carry equivalent overlay additions.
    same id + same semantic payload → composed once, all contributors kept
    in provenance. same id + divergent semantics → CompositionConflict and
    the earlier (canonical order) contribution stays — never silent skip,
    never last-write-wins.
    """
    reconciled = copy.deepcopy(scoped_overlay)
    conflicts: list[dict[str, Any]] = []
    notes: list[dict[str, Any]] = []

    nodes_by_id = {
        str(n["id"]): n
        for n in composed.get("nodes", [])
        if isinstance(n, dict) and n.get("id")
    }
    edges_by_id = {
        str(e["id"]): e
        for e in composed.get("edges", [])
        if isinstance(e, dict) and e.get("id")
    }

    kept_nodes: list[dict[str, Any]] = []
    for node in reconciled.get("extra_nodes") or []:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        nid = str(node["id"])
        existing = nodes_by_id.get(nid)
        if existing is None:
            # New element — applied downstream; provenance is recorded once
            # by the touched-tracking loop in compose_for_processo.
            kept_nodes.append(node)
            continue
        if _node_semantic_signature(existing) == _node_semantic_signature(node):
            provenance.setdefault(nid, []).append(
                {**contributor, "deduplicated": True}
            )
            if _node_geometry_signature(existing) != _node_geometry_signature(node):
                notes.append(
                    {
                        "element_id": nid,
                        "object_kind": "node",
                        "reason": "geometry_divergence",
                        "contributor": dict(contributor),
                    }
                )
            continue
        prior = [c for c in provenance.get(nid, []) if isinstance(c, dict)]
        conflicts.append(
            _conflict_entry(
                object_id=nid,
                object_kind="node",
                field="extra_node",
                reason="same_identity_divergent_semantics",
                winner_revisao_id=(prior[-1].get("revisao_id") if prior else None),
                contributors=[*prior, dict(contributor)],
            )
        )
    reconciled["extra_nodes"] = kept_nodes

    kept_edges: list[dict[str, Any]] = []
    for edge in reconciled.get("extra_edges") or []:
        if not isinstance(edge, dict) or not edge.get("id"):
            continue
        eid = str(edge["id"])
        existing = edges_by_id.get(eid)
        if existing is None:
            kept_edges.append(edge)
            continue
        if _edge_semantic_signature(existing) == _edge_semantic_signature(edge):
            provenance.setdefault(eid, []).append(
                {**contributor, "deduplicated": True}
            )
            continue
        prior = [c for c in provenance.get(eid, []) if isinstance(c, dict)]
        conflicts.append(
            _conflict_entry(
                object_id=eid,
                object_kind="edge",
                field="extra_edge",
                reason="same_identity_divergent_semantics",
                winner_revisao_id=(prior[-1].get("revisao_id") if prior else None),
                contributors=[*prior, dict(contributor)],
            )
        )
    reconciled["extra_edges"] = kept_edges
    return reconciled, conflicts, notes


class DiagramaCompositionService:
    """Compõe diagrama do processo na data D com overlays das revisões vigentes."""

    def __init__(self) -> None:
        self._merge = RevisaoDiagramMergeService()
        self._mermaid = DiagramMermaidExportService()

    def compose_for_processo(
        self,
        processo_id: str,
        *,
        at: date | None = None,
        instancia_id: str | None = None,
    ) -> dict[str, Any]:
        at = at or date.today()
        macro_row = ProcessoDiagramRepository().get(processo_id)
        macro_raw = (macro_row or {}).get("conteudo") if macro_row else None
        base = copy.deepcopy(validate_flowchart_v1(macro_raw or empty_flowchart()))
        base_ids = {
            str(n["id"])
            for n in base.get("nodes", [])
            if isinstance(n, dict) and n.get("id")
        }

        revisoes = RevisaoRepository().list_by_processo(processo_id)
        if instancia_id:
            revisoes = [
                r for r in revisoes if str(r.get("instancia_id") or "") == str(instancia_id)
            ]

        vigentes = sorted(
            [r for r in revisoes if revisao_vigente_em(r, at)],
            key=_sort_key_revisao,
        )

        composed = copy.deepcopy(base)
        applied: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        provenance: dict[str, list[dict[str, Any]]] = {}
        contributions: list[dict[str, Any]] = []
        composition_notes: list[dict[str, Any]] = []
        last_writer: dict[str, dict[str, Any]] = {}
        last_writer_edges: dict[str, dict[str, Any]] = {}

        for revisao in vigentes:
            revisao_id = str(revisao.get("revisao_id") or "")
            inst_id = str(revisao.get("instancia_id") or "")
            escopo_row = InstanciaDiagramEscopoRepository().get(inst_id) if inst_id else None
            escopo = validate_escopo(
                {
                    "node_ids": (escopo_row or {}).get("node_ids") or [],
                    "inherit_all": bool((escopo_row or {}).get("inherit_all", True))
                    if escopo_row
                    else True,
                    "include_boundary_edges": bool(
                        (escopo_row or {}).get("include_boundary_edges", False)
                    )
                    if escopo_row
                    else False,
                }
                if escopo_row
                else empty_escopo(),
                macro_node_ids=base_ids,
            )
            # Composição no macro completo; escopo só limita quais overrides contam
            overlay_row = RevisaoDiagramOverlayRepository().get(revisao_id)
            overlay = validate_overlay_v1(
                (overlay_row or {}).get("conteudo") if overlay_row else empty_overlay()
            )
            if RevisaoDiagramMergeService.overlay_is_empty(overlay):
                continue

            allowed = (
                base_ids
                if escopo.get("inherit_all", True)
                else set(escopo.get("node_ids") or [])
            )

            before_by_id = {
                str(n["id"]): copy.deepcopy(n)
                for n in composed.get("nodes", [])
                if isinstance(n, dict) and n.get("id")
            }

            # Aplica overlay só nos nós do escopo: filtra overrides fora do allowed
            scoped_overlay = copy.deepcopy(overlay)
            scoped_overlay["node_overrides"] = {
                k: v
                for k, v in (overlay.get("node_overrides") or {}).items()
                if str(k) in allowed
                or str(k)
                in {
                    str(n.get("id"))
                    for n in (overlay.get("extra_nodes") or [])
                    if isinstance(n, dict)
                }
            }
            scoped_overlay["removed_node_ids"] = [
                nid for nid in (overlay.get("removed_node_ids") or []) if str(nid) in allowed
            ]

            # G8-COMP-1 — every in-scope contribution is fingerprinted so the
            # migration seal stays sensitive to ALL sources, even ones whose
            # elements get deduplicated as equivalent.
            if not RevisaoDiagramMergeService.overlay_is_empty(scoped_overlay):
                contributions.append(
                    {
                        "revisao_id": revisao_id,
                        "instancia_id": inst_id,
                        "versao_revisao": revisao.get("versao_revisao"),
                        "overlay_sha256": _overlay_content_sha(scoped_overlay),
                    }
                )
            contributor = {
                "revisao_id": revisao_id,
                "instancia_id": inst_id,
                "versao_revisao": revisao.get("versao_revisao"),
            }

            # same-id extra elements: equivalent → dedup + provenance;
            # divergent → composition conflict (fail-closed for consumers
            # like the BPMN migration PREPARE).
            scoped_overlay, extra_conflicts, extra_notes = _reconcile_extras(
                scoped_overlay,
                composed=composed,
                contributor=contributor,
                provenance=provenance,
            )
            conflicts.extend(extra_conflicts)
            composition_notes.extend(extra_notes)

            # remove-vs-modify: an element already removed by an earlier
            # revision cannot be silently overridden by a later one.
            for nid in scoped_overlay.get("node_overrides") or {}:
                prev = last_writer.get(str(nid))
                if prev and prev.get("signature") == _ABSENT_SIG:
                    conflicts.append(
                        _conflict_entry(
                            object_id=str(nid),
                            object_kind="node",
                            field="removed",
                            reason="remove_vs_modify",
                            winner_revisao_id=prev.get("revisao_id"),
                            contributors=[
                                {
                                    "revisao_id": prev.get("revisao_id"),
                                    "instancia_id": prev.get("instancia_id"),
                                    "versao_revisao": prev.get("versao_revisao"),
                                },
                                dict(contributor),
                            ],
                        )
                    )
            for eid in scoped_overlay.get("edge_overrides") or {}:
                prev = last_writer_edges.get(str(eid))
                if prev and prev.get("signature") == _ABSENT_SIG:
                    conflicts.append(
                        _conflict_entry(
                            object_id=str(eid),
                            object_kind="edge",
                            field="removed",
                            reason="remove_vs_modify",
                            winner_revisao_id=prev.get("revisao_id"),
                            contributors=[
                                {
                                    "revisao_id": prev.get("revisao_id"),
                                    "instancia_id": prev.get("instancia_id"),
                                    "versao_revisao": prev.get("versao_revisao"),
                                },
                                dict(contributor),
                            ],
                        )
                    )

            # equivalent repeated removal → dedup with provenance
            for nid in scoped_overlay.get("removed_node_ids") or []:
                prev = last_writer.get(str(nid))
                if prev and prev.get("signature") == _ABSENT_SIG:
                    provenance.setdefault(str(nid), []).append(
                        {**contributor, "deduplicated": True}
                    )
            for eid in scoped_overlay.get("removed_edge_ids") or []:
                prev = last_writer_edges.get(str(eid))
                if prev and prev.get("signature") == _ABSENT_SIG:
                    provenance.setdefault(str(eid), []).append(
                        {**contributor, "deduplicated": True}
                    )

            before_edges_by_id = {
                str(e["id"]): copy.deepcopy(e)
                for e in composed.get("edges", [])
                if isinstance(e, dict) and e.get("id")
            }

            next_flow = self._merge.apply_overlay_to_flowchart(composed, scoped_overlay)
            after_by_id = {
                str(n["id"]): n
                for n in next_flow.get("nodes", [])
                if isinstance(n, dict) and n.get("id")
            }
            after_edges_by_id = {
                str(e["id"]): e
                for e in next_flow.get("edges", [])
                if isinstance(e, dict) and e.get("id")
            }

            touched: list[str] = []
            candidate_ids = (
                set(before_by_id)
                | set(after_by_id)
                | {str(x) for x in (scoped_overlay.get("removed_node_ids") or [])}
                | {
                    str(n["id"])
                    for n in (scoped_overlay.get("extra_nodes") or [])
                    if isinstance(n, dict) and n.get("id")
                }
                | {str(x) for x in (scoped_overlay.get("node_overrides") or {})}
            )

            node_overrides = scoped_overlay.get("node_overrides") or {}
            edge_override_keys = set(scoped_overlay.get("edge_overrides") or {})

            for node_id in candidate_ids:
                before = before_by_id.get(node_id)
                after = after_by_id.get(node_id)
                before_sig = _node_signature(before, present=before is not None)
                after_sig = _node_signature(after, present=after is not None)
                if before_sig == after_sig:
                    # same target + same resulting value → merge + provenance
                    # (cross-instance equivalent override — §21 G8-COMP-1).
                    if node_id in node_overrides and not any(
                        c.get("revisao_id") == contributor["revisao_id"]
                        for c in provenance.get(node_id, [])
                        if isinstance(c, dict)
                    ):
                        entry = dict(contributor)
                        if provenance.get(node_id):
                            entry["deduplicated"] = True
                        provenance.setdefault(node_id, []).append(entry)
                    continue
                is_extra = node_id not in base_ids
                if node_id not in allowed and not is_extra:
                    continue
                touched.append(node_id)
                prev = last_writer.get(node_id)
                if prev and prev.get("signature") != after_sig:
                    field = "removed" if after is None or before is None else "label"
                    conflicts.append(
                        {
                            "node_id": node_id,
                            "field": field,
                            "winner_revisao_id": revisao_id,
                            "revisoes": [
                                {
                                    "revisao_id": prev["revisao_id"],
                                    "versao_revisao": prev.get("versao_revisao"),
                                },
                                {
                                    "revisao_id": revisao_id,
                                    "versao_revisao": revisao.get("versao_revisao"),
                                    "label": (after or {}).get("label") if after else None,
                                },
                            ],
                        }
                    )
                last_writer[node_id] = {
                    "revisao_id": revisao_id,
                    "instancia_id": inst_id,
                    "versao_revisao": revisao.get("versao_revisao"),
                    "signature": after_sig,
                }
                provenance.setdefault(node_id, []).append(dict(contributor))

            # Edges get the same governance: divergent same-id contributions
            # are conflicts, never silent last-write-wins (G8-COMP-1).
            edge_candidate_ids = (
                set(before_edges_by_id)
                | set(after_edges_by_id)
                | {str(x) for x in (scoped_overlay.get("removed_edge_ids") or [])}
                | {
                    str(e["id"])
                    for e in (scoped_overlay.get("extra_edges") or [])
                    if isinstance(e, dict) and e.get("id")
                }
                | {str(x) for x in (scoped_overlay.get("edge_overrides") or {})}
            )
            touched_edges: list[str] = []
            for edge_id in edge_candidate_ids:
                before_e = before_edges_by_id.get(edge_id)
                after_e = after_edges_by_id.get(edge_id)
                before_esig = _edge_state_signature(before_e)
                after_esig = _edge_state_signature(after_e)
                if before_esig == after_esig:
                    if edge_id in edge_override_keys and not any(
                        c.get("revisao_id") == contributor["revisao_id"]
                        for c in provenance.get(edge_id, [])
                        if isinstance(c, dict)
                    ):
                        entry = dict(contributor)
                        if provenance.get(edge_id):
                            entry["deduplicated"] = True
                        provenance.setdefault(edge_id, []).append(entry)
                    continue
                touched_edges.append(edge_id)
                provenance.setdefault(edge_id, []).append(dict(contributor))
                prev = last_writer_edges.get(edge_id)
                if prev and prev.get("signature") != after_esig:
                    conflicts.append(
                        _conflict_entry(
                            object_id=edge_id,
                            object_kind="edge",
                            field="removed"
                            if after_e is None or before_e is None
                            else "edge",
                            reason="same_identity_divergent_semantics",
                            winner_revisao_id=revisao_id,
                            contributors=[
                                {
                                    "revisao_id": prev.get("revisao_id"),
                                    "instancia_id": prev.get("instancia_id"),
                                    "versao_revisao": prev.get("versao_revisao"),
                                },
                                dict(contributor),
                            ],
                        )
                    )
                last_writer_edges[edge_id] = {
                    "revisao_id": revisao_id,
                    "instancia_id": inst_id,
                    "versao_revisao": revisao.get("versao_revisao"),
                    "signature": after_esig,
                }

            composed = next_flow
            if touched or touched_edges:
                applied.append(
                    {
                        "revisao_id": revisao_id,
                        "instancia_id": inst_id,
                        "versao_revisao": revisao.get("versao_revisao"),
                        "cenario_tipo": revisao.get("cenario_tipo"),
                        "data_inicio_vigencia": str(revisao.get("data_inicio_vigencia") or "")[:10],
                        "node_ids_tocados": sorted(set(touched)),
                        "edge_ids_tocados": sorted(set(touched_edges)),
                    }
                )

        mermaid = self._mermaid.flowchart_to_mermaid(composed)
        return {
            "processo_id": processo_id,
            "at": at.isoformat(),
            "instancia_id": instancia_id,
            "flowchart": composed,
            "mermaid": mermaid,
            "applied_revisoes": applied,
            "conflicts": conflicts,
            "provenance": provenance,
            "contributions": contributions,
            "composition_notes": composition_notes,
            "base_node_count": len(base_ids),
        }
