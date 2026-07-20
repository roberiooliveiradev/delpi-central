"""Playbook 23 — composição temporal do macro WBS (base + deltas vigentes)."""

from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

from tm_app.application.services.revisao_decomposicao_merge_service import (
    RevisaoDecomposicaoMergeService,
)
from tm_app.domain import calc_rules
from tm_app.domain.decomposition.decomposition_tree_v1 import (
    empty_escopo,
    empty_overlay,
    empty_tree,
    expand_escopo_node_ids,
    tree_node_ids,
    validate_decomposition_escopo,
    validate_decomposition_overlay_v1,
    validate_decomposition_tree_v1,
)
from tm_app.infrastructure.persistence.repositories.instancia_decomposicao_escopo_repository import (
    InstanciaDecomposicaoEscopoRepository,
)
from tm_app.infrastructure.persistence.repositories.processo_decomposicao_repository import (
    ProcessoDecomposicaoRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_decomposicao_overlay_repository import (
    RevisaoDecomposicaoOverlayRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def revisao_vigente_em(revisao: dict[str, Any], at: date) -> bool:
    """Janela de composição: início ≤ at e (sem fim ou fim ≥ at). Baseline não compõe."""
    cenario = str(revisao.get("cenario_tipo") or "").lower()
    if cenario == "baseline" or cenario not in calc_rules.COMPARABLE_SCENARIOS:
        return False
    if revisao.get("deletado"):
        return False
    start = _parse_date(revisao.get("data_inicio_vigencia"))
    end = _parse_date(revisao.get("data_fim_vigencia"))
    if start is None or at < start:
        return False
    if end is not None and at > end:
        return False
    return True


def _sort_key_revisao(revisao: dict[str, Any]) -> tuple:
    start = _parse_date(revisao.get("data_inicio_vigencia")) or date.min
    versao = str(revisao.get("versao_revisao") or "")
    return (start, versao)


def _node_signature(node: dict[str, Any] | None, *, present: bool) -> tuple:
    if not present or node is None:
        return ("absent",)
    return (
        "present",
        str(node.get("label") or ""),
        str(node.get("parent_id") or ""),
        int(node.get("ordem") or 0),
        str(node.get("highlight") or ""),
    )


class DecomposicaoCompositionService:
    """Compõe árvore do processo na data D com overlays das revisões vigentes."""

    def __init__(self) -> None:
        self._merge = RevisaoDecomposicaoMergeService()

    def compose_for_processo(
        self,
        processo_id: str,
        *,
        at: date | None = None,
        instancia_id: str | None = None,
    ) -> dict[str, Any]:
        at = at or date.today()
        tree_row = ProcessoDecomposicaoRepository().get(processo_id)
        base_raw = (tree_row or {}).get("conteudo") if tree_row else None
        base = copy.deepcopy(validate_decomposition_tree_v1(base_raw or empty_tree()))
        base_ids = tree_node_ids(base)

        revisoes = RevisaoRepository().list_by_processo(processo_id)
        if instancia_id:
            revisoes = [
                r for r in revisoes if str(r.get("instancia_id") or "") == str(instancia_id)
            ]

        vigentes = sorted(
            [r for r in revisoes if revisao_vigente_em(r, at)],
            key=_sort_key_revisao,
        )

        composed_nodes = copy.deepcopy(
            [n for n in base.get("nodes", []) if isinstance(n, dict)]
        )
        applied: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        last_writer: dict[str, dict[str, Any]] = {}

        for revisao in vigentes:
            revisao_id = str(revisao.get("revisao_id") or "")
            inst_id = str(revisao.get("instancia_id") or "")
            escopo_row = InstanciaDecomposicaoEscopoRepository().get(inst_id) if inst_id else None
            escopo = validate_decomposition_escopo(
                {
                    "node_ids": (escopo_row or {}).get("node_ids") or [],
                    "inherit_all": bool((escopo_row or {}).get("inherit_all", True))
                    if escopo_row
                    else True,
                    "include_descendants": bool(
                        (escopo_row or {}).get("include_descendants", True)
                    )
                    if escopo_row
                    else True,
                }
                if escopo_row
                else empty_escopo(),
                tree_node_ids_set=base_ids,
            )
            overlay_row = RevisaoDecomposicaoOverlayRepository().get(revisao_id)
            overlay = validate_decomposition_overlay_v1(
                (overlay_row or {}).get("conteudo") if overlay_row else empty_overlay()
            )
            allowed = expand_escopo_node_ids(base, escopo)

            before_by_id = {
                str(n["id"]): copy.deepcopy(n)
                for n in composed_nodes
                if isinstance(n, dict) and n.get("id")
            }

            next_nodes = self._merge.apply_overlay_to_nodes(
                composed_nodes,
                overlay,
                allowed_base_ids=allowed,
            )
            after_by_id = {
                str(n["id"]): n
                for n in next_nodes
                if isinstance(n, dict) and n.get("id")
            }

            touched: list[str] = []
            candidate_ids = (
                set(before_by_id)
                | set(after_by_id)
                | {str(x) for x in (overlay.get("disabled_node_ids") or [])}
                | {str(n["id"]) for n in (overlay.get("extra_nodes") or []) if n.get("id")}
                | {str(x) for x in (overlay.get("node_overrides") or {})}
            )

            for node_id in candidate_ids:
                before = before_by_id.get(node_id)
                after = after_by_id.get(node_id)
                before_sig = _node_signature(before, present=before is not None)
                after_sig = _node_signature(after, present=after is not None)
                if before_sig == after_sig:
                    continue
                # só conta toque se o nó base está no escopo ou é extra desta revisão
                is_extra = node_id not in base_ids
                if node_id not in allowed and not is_extra:
                    continue
                if is_extra and node_id not in {
                    str(n["id"]) for n in (overlay.get("extra_nodes") or []) if n.get("id")
                }:
                    # extra de outra revisão — só conta se disable/override desta
                    if node_id not in (overlay.get("node_overrides") or {}) and node_id not in set(
                        overlay.get("disabled_node_ids") or []
                    ):
                        continue

                touched.append(node_id)
                prev = last_writer.get(node_id)
                if prev and prev.get("signature") != after_sig:
                    field = "disabled" if after is None or before is None else "structure"
                    if (
                        before is not None
                        and after is not None
                        and str(before.get("label")) != str(after.get("label"))
                    ):
                        field = "label"
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

            composed_nodes = next_nodes
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

        conflict_node_ids = {c["node_id"] for c in conflicts}
        for node in composed_nodes:
            if not isinstance(node, dict) or not node.get("id"):
                continue
            node_id = str(node["id"])
            writer = last_writer.get(node_id)
            if not writer:
                continue
            meta = dict(node.get("meta") or {})
            meta["composition"] = {
                "revisao_ids": [writer["revisao_id"]],
                "conflict": node_id in conflict_node_ids,
            }
            node["meta"] = meta

        return {
            "processo_id": processo_id,
            "at": at.isoformat(),
            "instancia_id": instancia_id,
            "tree": {**base, "nodes": composed_nodes},
            "applied_revisoes": applied,
            "conflicts": conflicts,
            "base_node_count": len(base_ids),
        }
