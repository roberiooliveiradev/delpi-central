"""Playbook 19 S7 — composição temporal do diagrama macro (base + deltas vigentes)."""

from __future__ import annotations

import copy
from datetime import date
from typing import Any

from tm_app.application.services.diagram_mermaid_export_service import DiagramMermaidExportService
from tm_app.application.services.decomposicao_composition_service import (
    revisao_vigente_em,
)
from tm_app.application.services.revisao_diagram_merge_service import RevisaoDiagramMergeService
from tm_app.domain.diagram.flowchart_v1 import (
    empty_escopo,
    empty_flowchart,
    empty_overlay,
    validate_escopo,
    validate_flowchart_v1,
    validate_overlay_v1,
)
from tm_app.infrastructure.persistence.repositories.instancia_diagram_escopo_repository import (
    InstanciaDiagramEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_diagram_repository import (
    ProcessoDiagramRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_diagram_overlay_repository import (
    RevisaoDiagramOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository


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
    return (start, versao)


def _node_signature(node: dict[str, Any] | None, *, present: bool) -> tuple:
    if not present or node is None:
        return ("absent",)
    return (
        "present",
        str(node.get("label") or ""),
        str(node.get("type") or ""),
        str(node.get("highlight") or ""),
    )


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
        last_writer: dict[str, dict[str, Any]] = {}

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

            next_flow = self._merge.apply_overlay_to_flowchart(composed, scoped_overlay)
            after_by_id = {
                str(n["id"]): n
                for n in next_flow.get("nodes", [])
                if isinstance(n, dict) and n.get("id")
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

            for node_id in candidate_ids:
                before = before_by_id.get(node_id)
                after = after_by_id.get(node_id)
                before_sig = _node_signature(before, present=before is not None)
                after_sig = _node_signature(after, present=after is not None)
                if before_sig == after_sig:
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
                    "versao_revisao": revisao.get("versao_revisao"),
                    "signature": after_sig,
                }

            composed = next_flow
            if touched:
                applied.append(
                    {
                        "revisao_id": revisao_id,
                        "instancia_id": inst_id,
                        "versao_revisao": revisao.get("versao_revisao"),
                        "cenario_tipo": revisao.get("cenario_tipo"),
                        "data_inicio_vigencia": str(revisao.get("data_inicio_vigencia") or "")[:10],
                        "node_ids_tocados": sorted(set(touched)),
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
            "base_node_count": len(base_ids),
        }
