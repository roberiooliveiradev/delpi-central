"""Playbook 23 — composição temporal do macro WBS (base + deltas vigentes)."""

from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

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


class DecomposicaoCompositionService:
    """Compõe árvore do processo na data D com overlays das revisões vigentes."""

    def compose_for_processo(
        self,
        processo_id: str,
        *,
        at: date | None = None,
        instancia_id: str | None = None,
    ) -> dict[str, Any] | None:
        at = at or date.today()
        tree_row = ProcessoDecomposicaoRepository().get(processo_id)
        base_raw = (tree_row or {}).get("conteudo") if tree_row else None
        base = copy.deepcopy(validate_decomposition_tree_v1(base_raw or empty_tree()))

        revisoes = RevisaoRepository().list_by_processo(processo_id)
        if instancia_id:
            revisoes = [
                r for r in revisoes if str(r.get("instancia_id") or "") == str(instancia_id)
            ]

        vigentes = sorted(
            [r for r in revisoes if revisao_vigente_em(r, at)],
            key=_sort_key_revisao,
        )

        # Por nó: lista de contribuições (ordem cronológica)
        contributions: dict[str, list[dict[str, Any]]] = {}
        applied: list[dict[str, Any]] = []

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
                tree_node_ids_set=tree_node_ids(base),
            )
            overlay_row = RevisaoDecomposicaoOverlayRepository().get(revisao_id)
            overlay = validate_decomposition_overlay_v1(
                (overlay_row or {}).get("conteudo") if overlay_row else empty_overlay()
            )
            allowed = expand_escopo_node_ids(base, escopo)
            touched: list[str] = []

            overrides = overlay.get("node_overrides") or {}
            for node_id, override in overrides.items():
                nid = str(node_id)
                if nid not in allowed or not isinstance(override, dict):
                    continue
                touched.append(nid)
                contributions.setdefault(nid, []).append(
                    {
                        "revisao_id": revisao_id,
                        "instancia_id": inst_id,
                        "versao_revisao": revisao.get("versao_revisao"),
                        "cenario_tipo": revisao.get("cenario_tipo"),
                        "data_inicio_vigencia": str(revisao.get("data_inicio_vigencia") or "")[:10],
                        "label": override.get("label"),
                        "descricao": override.get("descricao"),
                        "highlight": override.get("highlight"),
                        "disabled": False,
                    }
                )

            for node_id in overlay.get("disabled_node_ids") or []:
                nid = str(node_id)
                if nid not in allowed:
                    continue
                touched.append(nid)
                contributions.setdefault(nid, []).append(
                    {
                        "revisao_id": revisao_id,
                        "instancia_id": inst_id,
                        "versao_revisao": revisao.get("versao_revisao"),
                        "cenario_tipo": revisao.get("cenario_tipo"),
                        "data_inicio_vigencia": str(revisao.get("data_inicio_vigencia") or "")[:10],
                        "label": None,
                        "descricao": None,
                        "highlight": "removed",
                        "disabled": True,
                    }
                )

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

        conflicts: list[dict[str, Any]] = []
        composed_nodes: list[dict[str, Any]] = []
        disabled_ids: set[str] = set()

        base_by_id = {
            str(n["id"]): n
            for n in base.get("nodes", [])
            if isinstance(n, dict) and n.get("id")
        }

        for node_id, contribs in contributions.items():
            label_contribs = [c for c in contribs if c.get("label")]
            disabled_contribs = [c for c in contribs if c.get("disabled")]
            distinct_labels = {str(c.get("label") or "") for c in label_contribs}
            if len(distinct_labels) > 1:
                winner = label_contribs[-1]
                conflicts.append(
                    {
                        "node_id": node_id,
                        "field": "label",
                        "winner_revisao_id": winner["revisao_id"],
                        "revisoes": [
                            {
                                "revisao_id": c["revisao_id"],
                                "versao_revisao": c.get("versao_revisao"),
                                "label": c.get("label"),
                            }
                            for c in label_contribs
                        ],
                    }
                )

            disabled_revisao_ids = {c["revisao_id"] for c in disabled_contribs}
            label_revisao_ids = {c["revisao_id"] for c in label_contribs}
            if len(disabled_revisao_ids) > 1 or (
                disabled_revisao_ids and (label_revisao_ids - disabled_revisao_ids)
            ):
                winner = contribs[-1]
                conflicts.append(
                    {
                        "node_id": node_id,
                        "field": "disabled",
                        "winner_revisao_id": winner["revisao_id"],
                        "revisoes": [
                            {
                                "revisao_id": c["revisao_id"],
                                "versao_revisao": c.get("versao_revisao"),
                                "disabled": bool(c.get("disabled")),
                                "label": c.get("label"),
                            }
                            for c in contribs
                        ],
                    }
                )

            winner = contribs[-1]
            if winner.get("disabled"):
                disabled_ids.add(node_id)

        conflict_node_ids = {c["node_id"] for c in conflicts}

        for node in base.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("id") or "")
            if node_id in disabled_ids:
                continue
            merged = copy.deepcopy(node)
            contribs = contributions.get(node_id) or []
            for contrib in contribs:
                if contrib.get("disabled"):
                    continue
                if contrib.get("label"):
                    merged["label"] = contrib["label"]
                if contrib.get("descricao") is not None:
                    merged["descricao"] = contrib["descricao"]
                if contrib.get("highlight"):
                    merged["highlight"] = contrib["highlight"]
            if contribs:
                meta = dict(merged.get("meta") or {})
                meta["composition"] = {
                    "revisao_ids": [c["revisao_id"] for c in contribs],
                    "conflict": node_id in conflict_node_ids,
                }
                merged["meta"] = meta
            composed_nodes.append(merged)

        return {
            "processo_id": processo_id,
            "at": at.isoformat(),
            "instancia_id": instancia_id,
            "tree": {**base, "nodes": composed_nodes},
            "applied_revisoes": applied,
            "conflicts": conflicts,
            "base_node_count": len(base_by_id),
        }
